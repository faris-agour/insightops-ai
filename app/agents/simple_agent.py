from app.tools.sales_tools import analyze_sales


def classify_task(query: str) -> str:
    normalized_query = query.lower()
    if "sales" in normalized_query:
        return "sales_analysis"
    return "unknown"


def run_agent(query: str) -> dict[str, object]:
    task = classify_task(query)

    if task == "sales_analysis":
        return {
            "task": task,
            "result": analyze_sales(),
            "message": "Basic sales analysis completed",
        }

    return {
        "task": task,
        "result": {},
        "message": "No matching simple tool for this query",
    }
