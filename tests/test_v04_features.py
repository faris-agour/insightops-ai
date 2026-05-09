import unittest

from app.analysis.advanced_analytics import (
    analyze_trend,
    detect_anomalies,
    forecast_revenue,
)
from app.core.cache import TTLCache
from app.core.circuit_breaker import CircuitBreaker
from app.core.metrics import MetricsRegistry
from app.services.query_history import QueryHistory


class TestAdvancedAnalytics(unittest.TestCase):
    def test_detect_anomalies_returns_structure(self) -> None:
        result = detect_anomalies(z_threshold=2.0)
        self.assertIn("anomalies", result)
        self.assertIn("method", result)
        self.assertEqual(result["method"], "z_score")
        self.assertIn("total_days_analyzed", result)
        self.assertGreaterEqual(result["total_days_analyzed"], 0)

    def test_forecast_revenue_horizon(self) -> None:
        result = forecast_revenue(horizon_days=5)
        self.assertEqual(result["method"], "linear_regression")
        self.assertEqual(result["horizon_days"], 5)
        self.assertEqual(len(result["forecast"]), 5)
        for entry in result["forecast"]:
            self.assertIn("date", entry)
            self.assertIn("predicted_revenue", entry)
            self.assertGreaterEqual(entry["predicted_revenue"], 0)

    def test_analyze_trend_returns_moving_average(self) -> None:
        result = analyze_trend(window=7)
        self.assertIn("moving_average", result)
        self.assertIn("trend", result)
        self.assertIn(result["trend"], {"increasing", "decreasing", "stable", "no_data"})


class TestCircuitBreaker(unittest.TestCase):
    def test_opens_after_threshold(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
        self.assertFalse(cb.is_open("groq"))
        cb.record_failure("groq")
        self.assertFalse(cb.is_open("groq"))
        cb.record_failure("groq")
        self.assertTrue(cb.is_open("groq"))

    def test_success_resets_failures(self) -> None:
        cb = CircuitBreaker(failure_threshold=2, cooldown_seconds=60)
        cb.record_failure("groq")
        cb.record_success("groq")
        cb.record_failure("groq")
        self.assertFalse(cb.is_open("groq"))


class TestTTLCache(unittest.TestCase):
    def test_caches_value(self) -> None:
        cache: TTLCache[int] = TTLCache(ttl_seconds=60)
        calls = {"count": 0}

        def loader() -> int:
            calls["count"] += 1
            return 42

        self.assertEqual(cache.get_or_set("k", loader), 42)
        self.assertEqual(cache.get_or_set("k", loader), 42)
        self.assertEqual(calls["count"], 1)

    def test_invalidate_clears(self) -> None:
        cache: TTLCache[int] = TTLCache(ttl_seconds=60)
        cache.get_or_set("k", lambda: 1)
        cache.invalidate("k")
        cache.get_or_set("k", lambda: 2)
        self.assertEqual(cache.get_or_set("k", lambda: 99), 2)


class TestMetrics(unittest.TestCase):
    def test_records_counters_and_latency(self) -> None:
        m = MetricsRegistry()
        m.increment("requests.total")
        m.increment("requests.total")
        m.record_latency(12.5)
        m.record_tokens("Groq", 100)
        m.record_provider_call("Groq", success=True)

        snapshot = m.snapshot()
        self.assertEqual(snapshot["counters"]["requests.total"], 2)
        self.assertEqual(snapshot["latency_ms"]["samples"], 1)
        self.assertEqual(snapshot["llm_tokens"]["total"], 100)
        self.assertEqual(snapshot["providers"]["Groq"]["calls"], 1)


class TestQueryHistory(unittest.TestCase):
    def test_add_and_list(self) -> None:
        history = QueryHistory(max_size=3)
        history.add("q1", "sales_report", "model-a", 10.0)
        history.add("q2", "top_product", "model-b", 12.0)
        entries = history.list(limit=10)
        self.assertEqual(len(entries), 2)
        self.assertEqual(entries[0]["query"], "q2")

    def test_max_size_truncates(self) -> None:
        history = QueryHistory(max_size=2)
        for i in range(5):
            history.add(f"q{i}", "task", "model", 1.0)
        entries = history.list(limit=10)
        self.assertEqual(len(entries), 2)


if __name__ == "__main__":
    unittest.main()
