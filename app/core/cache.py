import threading
import time
from typing import Any, Callable, Generic, TypeVar

T = TypeVar("T")


class TTLCache(Generic[T]):
    def __init__(self, ttl_seconds: int) -> None:
        self._ttl = ttl_seconds
        self._lock = threading.Lock()
        self._store: dict[str, tuple[float, T]] = {}

    def get_or_set(self, key: str, loader: Callable[[], T]) -> T:
        now = time.monotonic()
        with self._lock:
            entry = self._store.get(key)
            if entry is not None:
                expires_at, value = entry
                if expires_at > now:
                    return value

        value = loader()
        with self._lock:
            self._store[key] = (now + self._ttl, value)
        return value

    def invalidate(self, key: str | None = None) -> None:
        with self._lock:
            if key is None:
                self._store.clear()
            else:
                self._store.pop(key, None)

    def stats(self) -> dict[str, Any]:
        with self._lock:
            return {"size": len(self._store), "ttl_seconds": self._ttl}
