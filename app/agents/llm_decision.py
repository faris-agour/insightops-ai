import json
from typing import Any

from pydantic import ValidationError

from app.agents.llm_providers import LLMProviderError, get_providers_in_order
from app.agents.model_router import select_model
from app.agents.prompts import get_prompt_registry
from app.core import tracing
from app.core.circuit_breaker import CircuitBreaker
from app.core.config import get_settings
from app.core.logging_config import get_logger
from app.core.metrics import get_metrics
from app.core.pricing import estimate_cost
from app.schemas import LLMDecisionPayload

logger = get_logger(__name__)
_settings = get_settings()
_metrics = get_metrics()
_circuit_breaker = CircuitBreaker(
    failure_threshold=_settings.CIRCUIT_BREAKER_FAILURE_THRESHOLD,
    cooldown_seconds=_settings.CIRCUIT_BREAKER_COOLDOWN_SECONDS,
)


# Sourced from the versioned prompt registry (intent_router@v1).
SYSTEM_PROMPT = get_prompt_registry().get("intent_router").template

INTENT_TO_TOOL = {
    "sales_report": "get_sales_summary",
    "sales_status": "get_sales_status",
    "top_product": "get_top_product",
    "worst_product": "get_worst_product",
    "sales_by_region": "get_sales_by_region",
    "anomaly_detection": "detect_anomalies",
    "forecast_revenue": "forecast_revenue",
    "trend_analysis": "analyze_trend",
    "unknown": "none",
}


class LLMDecisionError(RuntimeError):
    pass


def _sanitize_user_query(query: str) -> str:
    cleaned = query.replace("\x00", "").strip()
    if len(cleaned) > _settings.QUERY_MAX_LENGTH:
        cleaned = cleaned[: _settings.QUERY_MAX_LENGTH]
    return cleaned


def _extract_json_payload(raw_content: str) -> dict[str, Any]:
    raw_content = raw_content.strip()
    if not raw_content:
        raise LLMDecisionError("LLM returned empty output")

    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError as exc:
        decoder = json.JSONDecoder()
        start = raw_content.find("{")
        if start == -1:
            raise LLMDecisionError("LLM output is not valid JSON") from exc
        try:
            payload, _ = decoder.raw_decode(raw_content[start:])
        except json.JSONDecodeError as exc:
            raise LLMDecisionError("LLM output JSON parsing failed") from exc

    if not isinstance(payload, dict):
        raise LLMDecisionError("LLM output must be a JSON object")
    return payload


def _validate_decision(payload: dict[str, Any]) -> dict[str, str]:
    try:
        parsed = LLMDecisionPayload(**payload)
    except ValidationError as exc:
        raise LLMDecisionError(f"LLM payload failed validation: {exc.errors()[:2]}") from exc

    expected_tool = INTENT_TO_TOOL[parsed.intent]
    suggested = parsed.suggested_tool.strip().removesuffix("()")
    if suggested and suggested != expected_tool:
        raise LLMDecisionError(
            f"LLM returned mismatched tool: {suggested} (expected {expected_tool})"
        )

    reasoning = parsed.reasoning.strip() or "Intent inferred from query context."
    return {
        "intent": parsed.intent,
        "reasoning": reasoning,
        "suggested_tool": expected_tool,
    }


def decide_with_llm(query: str) -> dict[str, str]:
    if not _settings.LLM_ENABLED:
        raise LLMDecisionError("LLM decision layer is disabled")

    safe_query = _sanitize_user_query(query)
    if not safe_query:
        raise LLMDecisionError("Empty query after sanitization")

    model = select_model(safe_query)
    providers = get_providers_in_order()
    last_error: str | None = None

    for provider in providers:
        provider_name = provider.get_name()
        provider_key = provider_name.lower()

        if not provider.is_configured():
            continue

        if _circuit_breaker.is_open(provider_key):
            logger.warning("Circuit breaker open for %s, skipping", provider_name)
            continue

        timeout_seconds = _settings.PROVIDER_TIMEOUTS.get(
            provider_key, _settings.LLM_TIMEOUT_SECONDS
        )

        try:
            with tracing.span("llm_provider", provider=provider_name, model=model) as provider_span:
                response = provider.send_decision_request(
                    safe_query, SYSTEM_PROMPT, model, timeout_seconds
                )
                raw_content = response.get("content", "")
                tokens = int(response.get("total_tokens", 0) or 0)
                model_used = str(response.get("model", model))

                parsed_payload = _extract_json_payload(raw_content)
                decision = _validate_decision(parsed_payload)
                cost_usd = estimate_cost(model_used, tokens)
                decision["model_used"] = model_used
                decision["provider_used"] = provider_name
                decision["tokens"] = str(tokens)
                decision["cost_usd"] = f"{cost_usd:.6f}"
                provider_span.attributes.update(
                    {"intent": decision["intent"], "tokens": tokens, "cost_usd": cost_usd}
                )

            _circuit_breaker.record_success(provider_key)
            _metrics.record_provider_call(provider_name, success=True)
            _metrics.record_tokens(provider_name, tokens)
            _metrics.record_cost(model_used, cost_usd)
            logger.info(
                "LLM decision: provider=%s model=%s intent=%s tokens=%d cost=$%.6f",
                provider_name,
                model_used,
                decision["intent"],
                tokens,
                cost_usd,
            )
            return decision
        except (LLMProviderError, LLMDecisionError) as exc:
            last_error = str(exc)
            _circuit_breaker.record_failure(provider_key)
            _metrics.record_provider_call(provider_name, success=False)
            logger.warning("LLM provider %s failed: %s", provider_name, exc)
            continue

    if last_error:
        raise LLMDecisionError(f"All LLM providers failed. Last error: {last_error}")
    raise LLMDecisionError("No LLM providers are configured")


def get_circuit_breaker_state() -> dict[str, Any]:
    return _circuit_breaker.snapshot()
