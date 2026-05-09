import threading
import time
from collections import defaultdict, deque


class MetricsRegistry:
    def __init__(self, history_size: int = 100) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = defaultdict(int)
        self._latencies: deque[float] = deque(maxlen=history_size)
        self._tokens_total = 0
        self._tokens_by_provider: dict[str, int] = defaultdict(int)
        self._provider_calls: dict[str, int] = defaultdict(int)
        self._provider_failures: dict[str, int] = defaultdict(int)
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

    def snapshot(self) -> dict[str, object]:
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
                    "samples": len(latencies),
                },
                "llm_tokens": {
                    "total": self._tokens_total,
                    "by_provider": dict(self._tokens_by_provider),
                },
                "providers": {
                    name: {
                        "calls": self._provider_calls[name],
                        "failures": self._provider_failures[name],
                    }
                    for name in self._provider_calls
                },
            }


_registry: MetricsRegistry | None = None


def get_metrics() -> MetricsRegistry:
    global _registry
    if _registry is None:
        _registry = MetricsRegistry()
    return _registry
