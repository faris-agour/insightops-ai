import unittest

from app.agents.simple_agent import classify_task, run_agent
from app.main import AnalyzeRequest, analyze
from app.tools.sales_tools import (
    get_sales_by_region,
    get_sales_status,
    get_sales_summary,
    get_top_product,
    get_worst_product,
)


class TestAgentLoop(unittest.TestCase):
    def test_classify_task_report_queries(self) -> None:
        report_queries = [
            "sales report",
            "generate report",
            "summary of sales",
        ]
        for query in report_queries:
            with self.subTest(query=query):
                self.assertEqual(classify_task(query), "sales_report")

    def test_classify_task_status_queries(self) -> None:
        status_queries = [
            "how are sales doing",
            "sales performance",
            "current sales",
        ]
        for query in status_queries:
            with self.subTest(query=query):
                self.assertEqual(classify_task(query), "sales_status")

    def test_classify_task_unknown(self) -> None:
        self.assertEqual(classify_task("show trends for support tickets"), "unknown")

    def test_sales_summary_metrics(self) -> None:
        result = get_sales_summary()
        expected_fields = {
            "total_revenue",
            "average_daily_revenue",
            "top_product",
            "worst_product",
        }
        self.assertTrue(expected_fields.issubset(result.keys()))
        self.assertGreater(result["total_revenue"], 0)
        self.assertGreater(result["average_daily_revenue"], 0)
        self.assertIsInstance(result["top_product"], str)
        self.assertIsInstance(result["worst_product"], str)

    def test_top_product_query(self) -> None:
        result = run_agent("which product is selling the most")
        self.assertEqual(result["task"], "top_product")
        self.assertIn("product", result["result"])
        self.assertIn("revenue", result["result"])
        self.assertIn("insight", result)
        self.assertTrue(result["insight"])

    def test_sales_by_region(self) -> None:
        result = run_agent("compare regions")
        self.assertEqual(result["task"], "sales_by_region")
        self.assertIn("best_region", result["result"])
        self.assertIn("regions", result["result"])
        self.assertGreater(len(result["result"]["regions"]), 0)
        self.assertTrue(result["insight"])

    def test_fallback_behavior(self) -> None:
        result = run_agent("tell me about sales")
        self.assertEqual(result["task"], "sales_status")
        self.assertIn("trend", result["result"])

    def test_run_agent_unknown(self) -> None:
        result = run_agent("check customer churn")
        self.assertEqual(result["task"], "unknown")
        self.assertEqual(result["result"], {})
        self.assertIn("insight", result)

    def test_analyze_endpoint_top_product(self) -> None:
        response = analyze(AnalyzeRequest(query="best product"))
        self.assertEqual(response["task"], "top_product")
        self.assertIn("product", response["result"])
        self.assertIn("insight", response)

    def test_tools_return_structured_data(self) -> None:
        status = get_sales_status()
        top_product = get_top_product()
        worst_product = get_worst_product()
        by_region = get_sales_by_region()

        self.assertIn("trend", status)
        self.assertIn("product", top_product)
        self.assertIn("product", worst_product)
        self.assertIn("best_region", by_region)


if __name__ == "__main__":
    unittest.main()
