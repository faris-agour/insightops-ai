import threading
import time
from collections import deque
from typing import Any


class QueryHistory:
    def __init__(self, max_size: int = 100) -> None:
        self._lock = threading.Lock()
        self._entries: deque[dict[str, Any]] = deque(maxlen=max_size)

    def add(self, query: str, task: str, model_used: str, latency_ms: float) -> None:
        with self._lock:
            self._entries.append(
                {
                    "query": query,
                    "task": task,
                    "model_used": model_used,
                    "latency_ms": round(latency_ms, 2),
                    "timestamp": time.time(),
                }
            )

    def list(self, limit: int = 20) -> list[dict[str, Any]]:
        with self._lock:
            entries = list(self._entries)
        return entries[-limit:][::-1]

    def clear(self) -> None:
        with self._lock:
            self._entries.clear()


_history: QueryHistory | None = None


def get_history() -> QueryHistory:
    global _history
    if _history is None:
        from app.core.config import get_settings

        _history = QueryHistory(max_size=get_settings().QUERY_HISTORY_SIZE)
    return _history
