import re

from app.agents.llm_decision import LLMDecisionError, decide_with_llm
from app.tools.sales_tools import (
    get_sales_by_region,
    get_sales_status,
    get_sales_summary,
    get_top_product,
    get_worst_product,
)


SALES_KEYWORDS = {"sales", "sale", "revenue"}
REPORT_KEYWORDS = {"report", "summary", "overview"}
STATUS_KEYWORDS = {"status", "performance", "current", "doing", "trend"}
TOP_KEYWORDS = {"best", "top", "leading", "highest", "most"}
WORST_KEYWORDS = {"worst", "least", "lowest", "underperforming", "badly", "weakest"}
PRODUCT_KEYWORDS = {"product", "products", "item", "items", "sku"}
REGION_KEYWORDS = {"region", "regions", "area", "areas", "territory", "territories"}
COMPARE_KEYWORDS = {"compare", "comparison", "versus", "vs"}
GENERATE_KEYWORDS = {"generate", "create", "show", "give", "provide"}


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
            recommendation = "Investigate root causes—market saturation, competitive pressure, or internal issues—and take corrective action."
        else:
            summary = "Sales performance is holding steady with minor daily fluctuations."
            reasoning = (
                f"The relatively stable trend (daily change: {daily_change:.1f}%) suggests a balanced market "
                "environment without major disruptive factors."
            )
            recommendation = "Focus on incremental improvements to product offerings, customer retention, and operational efficiency."

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
            f"Maintain investment in {product} while leveraging its success to cross-sell and "
            "upsell complementary products to the same customer base."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "worst_product":
        product = str(result.get("product", "This product"))
        revenue = float(result.get("revenue", 0))
        pct_of_total = float(result.get("percent_of_total_revenue", 0))

        summary = f"{product} is underperforming relative to other offerings."
        reasoning = (
            f"At ${revenue:,.2f} ({pct_of_total:.1f}% of total revenue), {product} shows weak market adoption. "
            "This may signal product-market fit issues, poor positioning, or insufficient customer awareness."
        )
        recommendation = (
            f"Either reinvest in {product} with targeted improvements and marketing, or consider discontinuing "
            "it to free resources for higher-performing products."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    if task == "sales_by_region":
        best_region = str(result.get("best_region", "Unknown region"))
        best_revenue = float(result.get("best_region_revenue", 0))

        summary = f"Regional sales performance varies, with {best_region} leading the way."
        reasoning = (
            f"{best_region} generated ${best_revenue:,.2f}, representing the strongest regional execution. "
            "Geographic analysis reveals expansion opportunities in underperforming regions."
        )
        recommendation = (
            f"Analyze {best_region}'s success factors and replicate them in lower-performing regions. "
            "Consider targeted regional campaigns and localized sales strategies."
        )
        return f"{summary}\n\n{reasoning}\n\n{recommendation}"

    return "No matching analysis is available for this query yet."


TASK_HANDLERS = {
    "sales_report": get_sales_summary,
    "sales_status": get_sales_status,
    "top_product": get_top_product,
    "worst_product": get_worst_product,
    "sales_by_region": get_sales_by_region,
}


def run_agent(query: str) -> dict[str, object]:
    task: str
    model_used: str = "rule-based-fallback"

    try:
        llm_decision = decide_with_llm(query)
        task = llm_decision["intent"]
        model_used = llm_decision.get("model_used", "rule-based-fallback")
    except LLMDecisionError:
        task = classify_task(query)

    handler = TASK_HANDLERS.get(task)
    if handler:
        result = handler()
        return {
            "task": task,
            "result": result,
            "insight": build_insight(task, result),
            "model_used": model_used,
        }

    return {
        "task": task,
        "result": {},
        "insight": build_insight(task, {}),
        "model_used": model_used,
    }
