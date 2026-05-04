import unittest

from app.agents.simple_agent import classify_task, run_agent
from app.main import AnalyzeRequest, analyze
from app.tools.sales_tools import analyze_sales


class TestAgentLoop(unittest.TestCase):
    def test_classify_task_sales(self) -> None:
        sales_queries = [
            "Please analyze sales",
            "sales report",
            "how are sales doing",
            "analyze revenue",
        ]
        for query in sales_queries:
            with self.subTest(query=query):
                self.assertEqual(classify_task(query), "sales_analysis")

    def test_classify_task_unknown(self) -> None:
        self.assertEqual(classify_task("show trends for support tickets"), "unknown")

    def test_analyze_sales_metrics(self) -> None:
        result = analyze_sales()
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

    def test_run_agent_sales(self) -> None:
        result = run_agent("sales summary")
        self.assertEqual(result["task"], "sales_analysis")
        self.assertIn("average_daily_revenue", result["result"])
        self.assertIn("top_product", result["result"])
        self.assertIn("worst_product", result["result"])
        self.assertIn("insight", result)
        self.assertTrue(result["insight"])

    def test_run_agent_unknown(self) -> None:
        result = run_agent("check customer churn")
        self.assertEqual(result["task"], "unknown")
        self.assertEqual(result["result"], {})
        self.assertIn("insight", result)

    def test_analyze_endpoint(self) -> None:
        response = analyze(AnalyzeRequest(query="sales dashboard"))
        self.assertEqual(response["task"], "sales_analysis")
        self.assertIn("average_daily_revenue", response["result"])
        self.assertIn("insight", response)

    def test_analyze_response_contains_expected_fields_and_insight(self) -> None:
        response = analyze(AnalyzeRequest(query="analyze revenue"))
        self.assertTrue({"task", "result", "insight"}.issubset(response.keys()))
        self.assertTrue(
            {
                "total_revenue",
                "average_daily_revenue",
                "top_product",
                "worst_product",
            }.issubset(response["result"].keys())
        )
        self.assertTrue(response["insight"])


if __name__ == "__main__":
    unittest.main()
