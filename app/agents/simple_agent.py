import re

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
        return f"Sales report is ready. {top_product} is leading, while {worst_product} is trailing."

    if task == "sales_status":
        trend = str(result.get("trend", "stable"))
        if trend == "increasing":
            return "Sales are improving with a positive day-to-day trend."
        if trend == "decreasing":
            return "Sales are slowing down and need closer monitoring."
        return "Sales are stable with moderate variation across days."

    if task == "top_product":
        product = str(result.get("product", "This product"))
        return f"{product} is currently leading sales performance."

    if task == "worst_product":
        product = str(result.get("product", "This product"))
        return f"{product} is underperforming compared to other products."

    if task == "sales_by_region":
        best_region = str(result.get("best_region", "This region"))
        return f"Region {best_region} has the highest sales."

    return "No matching analysis is available for this query yet."


TASK_HANDLERS = {
    "sales_report": get_sales_summary,
    "sales_status": get_sales_status,
    "top_product": get_top_product,
    "worst_product": get_worst_product,
    "sales_by_region": get_sales_by_region,
}


def run_agent(query: str) -> dict[str, object]:
    task = classify_task(query)

    handler = TASK_HANDLERS.get(task)
    if handler:
        result = handler()
        return {
            "task": task,
            "result": result,
            "insight": build_insight(task, result),
        }

    return {
        "task": task,
        "result": {},
        "insight": build_insight(task, {}),
    }
