import json
import os
from typing import Any

from dotenv import load_dotenv

from app.agents.llm_providers import (
    LLMProviderError,
    get_providers_in_order,
)
from app.agents.model_router import select_model

load_dotenv()

DEFAULT_LLM_TIMEOUT_SECONDS = 5.0

SYSTEM_PROMPT = (
    "You are an intent router for a sales analytics backend. "
    "Classify the query into one intent: sales_report, sales_status, top_product, "
    "worst_product, sales_by_region, unknown. "
    "Return JSON only with keys: intent, reasoning, suggested_tool. "
    "Use suggested_tool names exactly as: get_sales_summary, get_sales_status, "
    "get_top_product, get_worst_product, get_sales_by_region, none."
)

ALLOWED_INTENTS = {
    "sales_report",
    "sales_status",
    "top_product",
    "worst_product",
    "sales_by_region",
    "unknown",
}
INTENT_TO_TOOL = {
    "sales_report": "get_sales_summary",
    "sales_status": "get_sales_status",
    "top_product": "get_top_product",
    "worst_product": "get_worst_product",
    "sales_by_region": "get_sales_by_region",
    "unknown": "none",
}


class LLMDecisionError(RuntimeError):
    pass


def _env_true(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _get_timeout_seconds() -> float:
    value = os.getenv("INSIGHTOPS_LLM_TIMEOUT_SECONDS", "").strip()
    if not value:
        return DEFAULT_LLM_TIMEOUT_SECONDS

    try:
        parsed = float(value)
    except ValueError:
        return DEFAULT_LLM_TIMEOUT_SECONDS

    return parsed if parsed > 0 else DEFAULT_LLM_TIMEOUT_SECONDS


def _extract_json_payload(raw_content: str) -> dict[str, Any]:
    raw_content = raw_content.strip()
    if not raw_content:
        raise LLMDecisionError("LLM returned empty output")

    try:
        payload = json.loads(raw_content)
    except json.JSONDecodeError:
        start = raw_content.find("{")
        end = raw_content.rfind("}")
        if start == -1 or end == -1 or start >= end:
            raise LLMDecisionError("LLM output is not valid JSON")

        try:
            payload = json.loads(raw_content[start : end + 1])
        except json.JSONDecodeError as exc:
            raise LLMDecisionError("LLM output JSON parsing failed") from exc

    if not isinstance(payload, dict):
        raise LLMDecisionError("LLM output must be a JSON object")

    return payload


def _validate_decision(payload: dict[str, Any]) -> dict[str, str]:
    intent = str(payload.get("intent", "")).strip()
    reasoning = str(payload.get("reasoning", "")).strip()
    suggested_tool = str(payload.get("suggested_tool", "")).strip().removesuffix("()")

    if intent not in ALLOWED_INTENTS:
        raise LLMDecisionError(f"Unsupported intent returned by LLM: {intent}")

    expected_tool = INTENT_TO_TOOL[intent]
    if suggested_tool and suggested_tool != expected_tool:
        raise LLMDecisionError(
            f"LLM returned mismatched tool: {suggested_tool} (expected {expected_tool})"
        )

    if not reasoning:
        reasoning = "Intent inferred from query context."

    return {
        "intent": intent,
        "reasoning": reasoning,
        "suggested_tool": expected_tool,
    }


def decide_with_llm(query: str) -> dict[str, str]:
    if not _env_true("INSIGHTOPS_LLM_ENABLED", default=False):
        raise LLMDecisionError("LLM decision layer is disabled")

    timeout_seconds = _get_timeout_seconds()
    model = select_model(query)

    providers = get_providers_in_order()
    last_error: str | None = None

    for provider in providers:
        if not provider.is_configured():
            continue

        try:
            response = provider.send_decision_request(query, SYSTEM_PROMPT, model, timeout_seconds)
            raw_content = response.get("content", "")
            parsed_payload = _extract_json_payload(raw_content)
            decision = _validate_decision(parsed_payload)
            decision["model_used"] = model
            decision["provider_used"] = provider.get_name()
            return decision
        except (LLMProviderError, LLMDecisionError) as exc:
            last_error = str(exc)
            continue

    if last_error:
        raise LLMDecisionError(f"All LLM providers failed. Last error: {last_error}")
    raise LLMDecisionError("No LLM providers are configured")
