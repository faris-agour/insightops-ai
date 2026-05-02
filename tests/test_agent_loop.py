import unittest

from app.agents.simple_agent import classify_task, run_agent
from app.main import AnalyzeRequest, analyze
from app.tools.sales_tools import analyze_sales


class TestAgentLoop(unittest.TestCase):
    def test_classify_task_sales(self) -> None:
        self.assertEqual(classify_task("Please analyze sales"), "sales_analysis")

    def test_classify_task_unknown(self) -> None:
        self.assertEqual(classify_task("show trends for support tickets"), "unknown")

    def test_analyze_sales_total_revenue(self) -> None:
        result = analyze_sales()
        self.assertEqual(result["total_revenue"], 11960.0)

    def test_run_agent_sales(self) -> None:
        result = run_agent("sales summary")
        self.assertEqual(result["task"], "sales_analysis")
        self.assertEqual(result["result"]["total_revenue"], 11960.0)
        self.assertEqual(result["message"], "Basic sales analysis completed")

    def test_run_agent_unknown(self) -> None:
        result = run_agent("check customer churn")
        self.assertEqual(result["task"], "unknown")
        self.assertEqual(result["result"], {})

    def test_analyze_endpoint(self) -> None:
        response = analyze(AnalyzeRequest(query="sales dashboard"))
        self.assertEqual(response["task"], "sales_analysis")
        self.assertEqual(response["result"]["total_revenue"], 11960.0)


if __name__ == "__main__":
    unittest.main()
