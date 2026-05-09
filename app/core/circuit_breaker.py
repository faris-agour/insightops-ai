import threading
import time
from dataclasses import dataclass


@dataclass
class CircuitState:
    failures: int = 0
    opened_at: float = 0.0


class CircuitBreaker:
    def __init__(self, failure_threshold: int, cooldown_seconds: int) -> None:
        self._threshold = failure_threshold
        self._cooldown = cooldown_seconds
        self._lock = threading.Lock()
        self._states: dict[str, CircuitState] = {}

    def _state(self, key: str) -> CircuitState:
        if key not in self._states:
            self._states[key] = CircuitState()
        return self._states[key]

    def is_open(self, key: str) -> bool:
        with self._lock:
            state = self._state(key)
            if state.failures < self._threshold:
                return False
            if time.monotonic() - state.opened_at >= self._cooldown:
                state.failures = 0
                state.opened_at = 0.0
                return False
            return True

    def record_success(self, key: str) -> None:
        with self._lock:
            state = self._state(key)
            state.failures = 0
            state.opened_at = 0.0

    def record_failure(self, key: str) -> None:
        with self._lock:
            state = self._state(key)
            state.failures += 1
            if state.failures >= self._threshold:
                state.opened_at = time.monotonic()

    def snapshot(self) -> dict[str, dict[str, float | int | bool]]:
        with self._lock:
            now = time.monotonic()
            return {
                key: {
                    "failures": state.failures,
                    "open": state.failures >= self._threshold
                    and (now - state.opened_at) < self._cooldown,
                    "cooldown_remaining": max(
                        0.0,
                        self._cooldown - (now - state.opened_at),
                    )
                    if state.opened_at > 0
                    else 0.0,
                }
                for key, state in self._states.items()
            }
