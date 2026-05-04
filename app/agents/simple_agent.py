import re

from app.tools.sales_tools import analyze_sales


SALES_PATTERNS = (
    r"\bsales?\b",
    r"\brevenue\b",
    r"\bsales?\s+(report|summary|analysis)\b",
    r"\bhow\s+are\s+sales\s+(doing|performing)\b",
    r"\banaly[sz]e\s+(sales|revenue)\b",
)


def classify_task(query: str) -> str:
    normalized_query = " ".join(query.lower().split())
    if any(re.search(pattern, normalized_query) for pattern in SALES_PATTERNS):
        return "sales_analysis"
    return "unknown"


def build_sales_insight(result: dict[str, object]) -> str:
    top_product = str(result.get("top_product", "Top product")).strip() or "Top product"
    worst_product = str(result.get("worst_product", "other products")).strip() or "other products"

    if top_product == worst_product:
        return f"Sales activity is concentrated around {top_product}."

    return (
        f"Sales are stable overall with {top_product} leading performance, "
        f"while {worst_product} shows weaker results."
    )


def run_agent(query: str) -> dict[str, object]:
    task = classify_task(query)

    if task == "sales_analysis":
        metrics = analyze_sales()
        return {
            "task": task,
            "result": metrics,
            "insight": build_sales_insight(metrics),
        }

    return {
        "task": task,
        "result": {},
        "insight": "No matching analysis is available for this query yet.",
    }
