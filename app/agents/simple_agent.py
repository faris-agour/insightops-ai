import re
import time

from app.agents.llm_decision import LLMDecisionError, decide_with_llm
from app.analysis.advanced_analytics import (
    analyze_trend,
    detect_anomalies,
    forecast_revenue,
)
from app.core import tracing
from app.core.guardrails import redact_pii, scan_input
from app.core.logging_config import get_logger
from app.core.metrics import get_metrics
from app.tools.sales_tools import (
    get_sales_by_region,
    get_sales_status,
    get_sales_summary,
    get_top_product,
    get_worst_product,
)

logger = get_logger(__name__)
_metrics = get_metrics()


SALES_KEYWORDS = {"sales", "sale", "revenue"}
REPORT_KEYWORDS = {"report", "summary", "overview"}
STATUS_KEYWORDS = {"status", "performance", "current", "doing"}
TOP_KEYWORDS = {"best", "top", "leading", "highest", "most"}
WORST_KEYWORDS = {"worst", "least", "lowest", "underperforming", "badly", "weakest"}
PRODUCT_KEYWORDS = {"product", "products", "item", "items", "sku"}
REGION_KEYWORDS = {"region", "regions", "area", "areas", "territory", "territories"}
COMPARE_KEYWORDS = {"compare", "comparison", "versus", "vs"}
GENERATE_KEYWORDS = {"generate", "create", "show", "give", "provide"}
ANOMALY_KEYWORDS = {"anomaly", "anomalies", "outlier", "outliers", "spike", "spikes", "drop", "unusual", "abnormal"}
FORECAST_KEYWORDS = {"forecast", "predict", "prediction", "projection", "future", "next"}
TREND_KEYWORDS = {"trend", "trending", "moving", "growth", "decline", "trajectory"}


def _tokenize(query: str) -> tuple[str, set[str]]:
    normalized_query = re.sub(r"[^a-z0-9\s]", " ", query.lower())
    normalized_query = " ".join(normalized_query.split())
    return normalized_query, set(normalized_query.split())


def _contains_any(tokens: set[str], keywords: set[str]) -> bool:
    return any(token in keywords for token in tokens)


def classify_task(query: str) -> str:
    normalized_query, tokens = _tokenize(query)
    if not tokens:
        return "unknown"

    if _contains_any(tokens, ANOMALY_KEYWORDS):
        return "anomaly_detection"

    if _contains_any(tokens, FORECAST_KEYWORDS):
        return "forecast_revenue"

    if _contains_any(tokens, TREND_KEYWORDS) and not _contains_any(tokens, STATUS_KEYWORDS):
        return "trend_analysis"

    has_sales_context = _contains_any(tokens, SALES_KEYWORDS)

    has_product_context = _contains_any(tokens, PRODUCT_KEYWORDS)
    has_top_signal = _contains_any(tokens, TOP_KEYWORDS) or ("selling" in tokens and "most" in tokens)
    if has_product_context and has_top_signal:
        return "top_product"

    has_worst_signal = _contains_any(tokens, WORST_KEYWORDS) or ("selling" in tokens and "least" in tokens)
    if has_product_context and has_worst_signal:
        return "worst_product"

    has_region_context = _contains_any(tokens, REGION_KEYWORDS)
    has_region_signal = _contains_any(tokens, COMPARE_KEYWORDS.union(TOP_KEYWORDS).union(WORST_KEYWORDS))
    if has_region_context and (has_sales_context or has_region_signal):
        return "sales_by_region"

    has_report_intent = _contains_any(tokens, REPORT_KEYWORDS) or (
        _contains_any(tokens, GENERATE_KEYWORDS) and "report" in tokens
    )
    if has_report_intent and (has_sales_context or "report" in tokens):
        return "sales_report"

    has_status_intent = _contains_any(tokens, STATUS_KEYWORDS) or "how are sales" in normalized_query
    if has_sales_context and has_status_intent:
        return "sales_status"

    if has_sales_context:
        return "sales_status"

    return "unknown"


def build_insight(task: str, result: dict[str, object]) -> str:
    if task == "sales_report":
        top_product = str(result.get("top_product", "Top product"))
        worst_product = str(result.get("worst_product", "other products"))
        total_revenue = float(result.get("total_revenue", 0))
        avg_daily = float(result.get("average_daily_revenue", 0))
        summary = f"{top_product} leads the portfolio while {worst_product} underperforms."
        reasoning = (
            f"With ${total_revenue:,.2f} in total revenue and ${avg_daily:,.2f} daily average, "
            "the portfolio concentration on top performers indicates opportunity to optimize underperformers."
        )
        recommendation = (
            f"Consider strategies to boost {worst_product}'s performance, such as improved marketing, "
            "pricing adjustments, or feature enhancements."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "sales_status":
        trend = str(result.get("trend", "stable"))
        daily_change = float(result.get("daily_change_percent", 0))
        if trend == "increasing":
            summary = "Sales momentum is positive with day-to-day growth."
            reasoning = f"The {daily_change:.1f}% daily increase indicates strong market demand and effective sales execution."
            recommendation = "Capitalize on this momentum by increasing inventory and marketing spend to maximize the uptrend."
        elif trend == "decreasing":
            summary = "Sales are declining and warrant immediate attention."
            reasoning = f"With a {abs(daily_change):.1f}% daily decrease, the trend suggests market headwinds or execution challenges."
            recommendation = "Investigate root causes and take corrective action."
        else:
            summary = "Sales performance is holding steady with minor daily fluctuations."
            reasoning = (
                f"The relatively stable trend (daily change: {daily_change:.1f}%) suggests a balanced market environment."
            )
            recommendation = "Focus on incremental improvements to product offerings and customer retention."
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "top_product":
        product = str(result.get("product", "This product"))
        revenue = float(result.get("revenue", 0))
        pct_of_total = float(result.get("percent_of_total_revenue", 0))
        summary = f"{product} is the top revenue generator in the portfolio."
        reasoning = (
            f"With ${revenue:,.2f} in revenue ({pct_of_total:.1f}% of total), {product} represents "
            "the strongest market segment and customer preference alignment."
        )
        recommendation = (
            f"Maintain investment in {product} while leveraging its success to cross-sell complementary products."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "worst_product":
        product = str(result.get("product", "This product"))
        revenue = float(result.get("revenue", 0))
        pct_of_total = float(result.get("percent_of_total_revenue", 0))
        summary = f"{product} is underperforming relative to other offerings."
        reasoning = (
            f"At ${revenue:,.2f} ({pct_of_total:.1f}% of total revenue), {product} shows weak market adoption."
        )
        recommendation = (
            f"Either reinvest in {product} with targeted improvements, or consider discontinuing it to free resources."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "sales_by_region":
        best_region = str(result.get("best_region", "Unknown region"))
        best_revenue = float(result.get("best_region_revenue", 0))
        summary = f"Regional sales performance varies, with {best_region} leading the way."
        reasoning = (
            f"{best_region} generated ${best_revenue:,.2f}, representing the strongest regional execution."
        )
        recommendation = (
            f"Analyze {best_region}'s success factors and replicate them in lower-performing regions."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "anomaly_detection":
        count = int(result.get("anomaly_count", 0) or 0)
        threshold = float(result.get("threshold", 2.0))
        if count == 0:
            summary = "No revenue anomalies detected in the analyzed window."
            reasoning = f"All daily revenues fall within {threshold} standard deviations of the mean — operations look stable."
            recommendation = "Maintain current operational cadence and continue monitoring."
        else:
            anomalies = result.get("anomalies", []) or []
            spikes = sum(1 for a in anomalies if isinstance(a, dict) and a.get("direction") == "spike")
            drops = count - spikes
            summary = f"{count} revenue anomalies detected ({spikes} spikes, {drops} drops)."
            reasoning = (
                f"Z-score analysis flagged days outside ±{threshold}σ of the mean, "
                "indicating unusual demand or operational events."
            )
            recommendation = "Investigate flagged dates for promotions, outages, or one-off events that drove the variance."
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "forecast_revenue":
        horizon = int(result.get("horizon_days", 0) or 0)
        direction = str(result.get("trend_direction", "flat"))
        slope = float(result.get("daily_growth_estimate", 0) or 0)
        summary = f"Revenue forecast for the next {horizon} days projects a {direction} trajectory."
        reasoning = (
            f"Linear regression on historical daily revenue yielded a slope of ${slope:,.2f} per day."
        )
        recommendation = (
            "Use this forecast for short-term planning; combine with anomaly detection for risk-aware decisions."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "trend_analysis":
        trend = str(result.get("trend", "stable"))
        change = float(result.get("change_percent", 0) or 0)
        window = int(result.get("window", 0) or 0)
        summary = f"Moving-average trend over a {window}-day window is {trend}."
        reasoning = f"Smoothed series shows a {change:+.1f}% change between the earliest and latest averages."
        recommendation = "Use the smoothed trend to filter daily noise and inform mid-term strategy."
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    return "No matching analysis is available for this query yet."


TASK_HANDLERS = {
    "sales_report": get_sales_summary,
    "sales_status": get_sales_status,
    "top_product": get_top_product,
    "worst_product": get_worst_product,
    "sales_by_region": get_sales_by_region,
    "anomaly_detection": detect_anomalies,
    "forecast_revenue": forecast_revenue,
    "trend_analysis": analyze_trend,
}


def run_agent(query: str) -> dict[str, object]:
    started = time.perf_counter()
    trace = tracing.start_trace(query)
    task: str
    model_used: str = "rule-based-fallback"
    provider_used: str | None = None
    tokens = 0
    cost_usd = 0.0

    with tracing.span("guardrails") as guard_span:
        guard = scan_input(query)
        guard_span.attributes["flagged"] = guard.flagged
        if guard.flagged:
            guard_span.attributes["reasons"] = guard.reasons
            _metrics.record_guardrail_flag()
            logger.warning(
                "Guardrail flagged query '%s': %s", redact_pii(query), guard.reasons
            )

    with tracing.span("decision") as decision_span:
        try:
            llm_decision = decide_with_llm(query)
            task = llm_decision["intent"]
            model_used = llm_decision.get("model_used", "rule-based-fallback")
            provider_used = llm_decision.get("provider_used")
            tokens = int(llm_decision.get("tokens", "0") or 0)
            cost_usd = float(llm_decision.get("cost_usd", "0") or 0.0)
            decision_span.attributes["path"] = "llm"
        except LLMDecisionError as exc:
            logger.info("LLM unavailable, falling back to rules: %s", exc)
            task = classify_task(query)
            decision_span.attributes["path"] = "rule_based"
        except Exception as exc:
            logger.exception("Unexpected error in LLM decision, falling back to rules: %s", exc)
            task = classify_task(query)
            decision_span.attributes["path"] = "rule_based"
        decision_span.attributes["task"] = task

    handler = TASK_HANDLERS.get(task)
    with tracing.span("tool_execution", tool=getattr(handler, "__name__", "none")):
        try:
            result: dict[str, object] = handler() if handler else {}
        except Exception as exc:
            logger.exception("Tool handler %s failed: %s", task, exc)
            result = {"error": "tool_execution_failed"}

    with tracing.span("insight"):
        insight = build_insight(task, result)

    latency_ms = (time.perf_counter() - started) * 1000.0
    _metrics.record_latency(latency_ms)
    _metrics.increment(f"task.{task}")
    _metrics.increment("requests.total")

    tracing.finish_trace(
        trace,
        task=task,
        model_used=model_used,
        provider_used=provider_used,
        latency_ms=round(latency_ms, 2),
        guardrail_flagged=guard.flagged,
    )

    return {
        "task": task,
        "result": result,
        "insight": insight,
        "model_used": model_used,
        "provider_used": provider_used,
        "latency_ms": round(latency_ms, 2),
        "trace_id": trace.trace_id,
        "tokens": tokens,
        "cost_usd": round(cost_usd, 6),
    }
