import threading
import time
from collections import defaultdict, deque
from typing import Any


class MetricsRegistry:
    def __init__(self, history_size: int = 100) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._latencies: deque[float] = deque(maxlen=history_size)
        self._tokens_total = 0
        self._tokens_by_provider: dict[str, int] = defaultdict(int)
        self._provider_calls: dict[str, int] = defaultdict(int)
        self._provider_failures: dict[str, int] = defaultdict(int)
        self._cost_total = 0.0
        self._cost_by_model: dict[str, float] = defaultdict(float)
        self._guardrail_flags = 0
        self._started_at = time.time()

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[name] += amount

    def record_latency(self, ms: float) -> None:
        with self._lock:
            self._latencies.append(ms)

    def record_tokens(self, provider: str, tokens: int) -> None:
        if tokens <= 0:
            return
        with self._lock:
            self._tokens_total += tokens
            self._tokens_by_provider[provider] += tokens

    def record_provider_call(self, provider: str, success: bool) -> None:
        with self._lock:
            self._provider_calls[provider] += 1
            if not success:
                self._provider_failures[provider] += 1

    def record_cost(self, model: str, usd: float) -> None:
        if usd <= 0:
            return
        with self._lock:
            self._cost_total += usd
            self._cost_by_model[model] += usd

    def record_guardrail_flag(self, amount: int = 1) -> None:
        with self._lock:
            self._guardrail_flags += amount

    def _percentile(self, values: list[float], pct: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        rank = max(0, min(len(ordered) - 1, round((pct / 100) * (len(ordered) - 1))))
        return round(ordered[rank], 2)

    def snapshot(self) -> dict[str, Any]:
        with self._lock:
            latencies = list(self._latencies)
            avg_latency = sum(latencies) / len(latencies) if latencies else 0.0
            return {
                "uptime_seconds": round(time.time() - self._started_at, 2),
                "counters": dict(self._counters),
                "latency_ms": {
                    "avg": round(avg_latency, 2),
                    "min": round(min(latencies), 2) if latencies else 0.0,
                    "max": round(max(latencies), 2) if latencies else 0.0,
                    "p50": self._percentile(latencies, 50),
                    "p95": self._percentile(latencies, 95),
                    "samples": len(latencies),
                },
                "llm_tokens": {
                    "total": self._tokens_total,
                    "by_provider": dict(self._tokens_by_provider),
                },
                "llm_cost_usd": {
                    "total": round(self._cost_total, 6),
                    "by_model": {k: round(v, 6) for k, v in self._cost_by_model.items()},
                },
                "guardrails": {"flagged_inputs": self._guardrail_flags},
                "providers": {
                    name: {
                        "calls": self._provider_calls[name],
                        "failures": self._provider_failures[name],
                    }
                    for name in self._provider_calls
                },
            }

    def prometheus(self) -> str:
        """Render core metrics in Prometheus text exposition format."""
        snap = self.snapshot()
        lines: list[str] = []

        def metric(name: str, value: float, help_text: str, mtype: str = "gauge") -> None:
            lines.append(f"# HELP {name} {help_text}")
            lines.append(f"# TYPE {name} {mtype}")
            lines.append(f"{name} {value}")

        metric("insightops_uptime_seconds", snap["uptime_seconds"], "Service uptime in seconds")
        latency = snap["latency_ms"]
        metric("insightops_latency_ms_avg", latency["avg"], "Average request latency (ms)")
        metric("insightops_latency_ms_p95", latency["p95"], "p95 request latency (ms)")
        metric(
            "insightops_llm_tokens_total",
            snap["llm_tokens"]["total"],
            "Total LLM tokens used",
            "counter",
        )
        metric(
            "insightops_llm_cost_usd_total",
            snap["llm_cost_usd"]["total"],
            "Estimated LLM cost (USD)",
            "counter",
        )
        metric(
            "insightops_guardrail_flagged_total",
            snap["guardrails"]["flagged_inputs"],
            "Inputs flagged by guardrails",
            "counter",
        )

        for key, value in snap["counters"].items():
            safe = key.replace(".", "_").replace("-", "_")
            lines.append(f'insightops_counter{{name="{safe}"}} {value}')
        for provider, stats in snap["providers"].items():
            lines.append(f'insightops_provider_calls{{provider="{provider}"}} {stats["calls"]}')
            lines.append(
                f'insightops_provider_failures{{provider="{provider}"}} {stats["failures"]}'
            )

        return "\n".join(lines) + "\n"


_registry: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry
