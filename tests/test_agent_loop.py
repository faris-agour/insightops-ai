import os
import unittest
from unittest.mock import patch

from app.agents.llm_decision import LLMDecisionError
from app.agents.llm_providers import (
    GroqProvider,
    HuggingFaceProvider,
    JetstreamProvider,
    get_providers_in_order,
)
from app.agents.model_router import select_model
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
    def setUp(self) -> None:
        self._env_patch = patch.dict(
            os.environ,
            {
                "INSIGHTOPS_LLM_ENABLED": "false",
                "GROQ_API_KEY": "",
                "HF_API_KEY": "",
                "JETSTREAM_API_KEY": "",
            },
            clear=False,
        )
        self._env_patch.start()

    def tearDown(self) -> None:
        self._env_patch.stop()

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

    def test_llm_decision_success_path(self) -> None:
        llm_decision = {
            "intent": "top_product",
            "reasoning": "Query asks for best selling product.",
            "suggested_tool": "get_top_product",
            "model_used": "gpt-4o-mini",
        }
        with patch("app.agents.simple_agent.decide_with_llm", return_value=llm_decision):
            result = run_agent("which product is selling the most")

        self.assertEqual(result["task"], "top_product")
        self.assertEqual(result.get("model_used"), "gpt-4o-mini")
        self.assertIn("product", result["result"])

    def test_llm_fallback_to_rule_based_path(self) -> None:
        with patch(
            "app.agents.simple_agent.decide_with_llm",
            side_effect=LLMDecisionError("timed out"),
        ):
            result = run_agent("sales report")

        self.assertEqual(result["task"], "sales_report")
        self.assertEqual(result.get("model_used"), "rule-based-fallback")

    def test_adaptive_model_selection(self) -> None:
        with patch.dict(
            os.environ,
            {
                "INSIGHTOPS_FAST_MODEL": "fast-test-model",
                "INSIGHTOPS_STRONG_MODEL": "strong-test-model",
                "INSIGHTOPS_STRONG_MODEL_MIN_TOKENS": "8",
                "INSIGHTOPS_STRONG_MODEL_KEYWORDS": "compare,explain",
            },
            clear=False,
        ):
            self.assertEqual(select_model("sales report"), "fast-test-model")
            self.assertEqual(
                select_model("compare sales by region and explain why performance differs"),
                "strong-test-model",
            )

    def test_provider_configuration_checks(self) -> None:
        groq = GroqProvider()
        hf = HuggingFaceProvider()
        jetstream = JetstreamProvider()

        self.assertFalse(groq.is_configured())
        self.assertFalse(hf.is_configured())
        self.assertFalse(jetstream.is_configured())

        self.assertEqual(groq.get_name(), "Groq")
        self.assertEqual(hf.get_name(), "HuggingFace")
        self.assertEqual(jetstream.get_name(), "Jetstream")

    def test_provider_order_default(self) -> None:
        providers = get_providers_in_order()
        self.assertTrue(len(providers) >= 3)
        self.assertIsInstance(providers[0], GroqProvider)
        self.assertIsInstance(providers[1], HuggingFaceProvider)
        self.assertIsInstance(providers[2], JetstreamProvider)

    def test_provider_order_custom(self) -> None:
        with patch.dict(
            os.environ,
            {"INSIGHTOPS_LLM_PROVIDER_ORDER": "jetstream,groq,huggingface"},
            clear=False,
        ):
            providers = get_providers_in_order()
            self.assertEqual(providers[0].get_name(), "Jetstream")
            self.assertEqual(providers[1].get_name(), "Groq")
            self.assertEqual(providers[2].get_name(), "HuggingFace")

    def test_run_agent_unknown(self) -> None:
        result = run_agent("check customer churn")
        self.assertEqual(result["task"], "unknown")
        self.assertEqual(result["result"], {})
        self.assertIn("insight", result)

    def test_analyze_endpoint_top_product(self) -> None:
        response = analyze(AnalyzeRequest(query="best product"))
        self.assertEqual(response.task, "top_product")
        self.assertIn("product", response.result)
        self.assertTrue(response.insight)

    def test_tools_return_structured_data(self) -> None:
        status = get_sales_status()
        top_product = get_top_product()
        worst_product = get_worst_product()
        by_region = get_sales_by_region()

        self.assertIn("trend", status)
        self.assertIn("product", top_product)
        self.assertIn("product", worst_product)
        self.assertIn("best_region", by_region)

    def test_richer_insight_format_top_product(self) -> None:
        result = run_agent("which product is selling the most")
        insight = result["insight"]
        self.assertIsInstance(insight, str)
        self.assertGreater(len(insight), 50)
        self.assertIn("\n", insight)
        self.assertIn("revenue generator", insight.lower())

    def test_richer_insight_format_sales_report(self) -> None:
        result = run_agent("sales report")
        insight = result["insight"]
        self.assertIsInstance(insight, str)
        self.assertGreater(len(insight), 50)
        self.assertIn("\n", insight)

    def test_richer_insight_format_sales_status(self) -> None:
        result = run_agent("how are sales")
        insight = result["insight"]
        self.assertIsInstance(insight, str)
        self.assertGreater(len(insight), 50)
        self.assertIn("\n", insight)

    def test_richer_insight_contains_recommendation(self) -> None:
        result = run_agent("best product")
        insight = result["insight"]
        self.assertIn("maintain", insight.lower())


if __name__ == "__main__":
    unittest.main()
