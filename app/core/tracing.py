"""Lightweight request tracing for LLMOps observability.

Provides a per-request ``Trace`` composed of timed ``Span``s. The current trace is
held in a :class:`contextvars.ContextVar` so deeply nested code (e.g. the LLM
decision layer or a specialized agent) can record spans without threading the
trace object through every call.

This is intentionally dependency-free (no OpenTelemetry) so the project stays
clone-and-run, while still demonstrating the tracing concepts reviewers expect.
"""

from __future__ import annotations

import time
import uuid
from collections import deque
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from typing import Any, Iterator


@dataclass
class Span:
    name: str
    start_ms: float
    end_ms: float | None = None
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    @property
    def duration_ms(self) -> float:
        if self.end_ms is None:
            return 0.0
        return round(self.end_ms - self.start_ms, 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "duration_ms": self.duration_ms,
            "status": self.status,
            "attributes": self.attributes,
        }


@dataclass
class Trace:
    trace_id: str
    query: str
    created_at: float
    spans: list[Span] = field(default_factory=list)
    attributes: dict[str, Any] = field(default_factory=dict)
    status: str = "ok"

    @property
    def total_ms(self) -> float:
        return round(sum(span.duration_ms for span in self.spans), 3)

    def to_dict(self) -> dict[str, Any]:
        return {
            "trace_id": self.trace_id,
            "query": self.query,
            "created_at": self.created_at,
            "status": self.status,
            "total_ms": self.total_ms,
            "attributes": self.attributes,
            "spans": [span.to_dict() for span in self.spans],
        }


_current_trace: ContextVar[Trace | None] = ContextVar("current_trace", default=None)


class TraceStore:
    """Bounded in-memory store of the most recent traces."""

    def __init__(self, max_size: int = 200) -> None:
        self._traces: deque[Trace] = deque(maxlen=max_size)
        self._by_id: dict[str, Trace] = {}

    def add(self, trace: Trace) -> None:
        if len(self._traces) == self._traces.maxlen and self._traces:
            evicted = self._traces[0]
            self._by_id.pop(evicted.trace_id, None)
        self._traces.append(trace)
        self._by_id[trace.trace_id] = trace

    def get(self, trace_id: str) -> Trace | None:
        return self._by_id.get(trace_id)

    def recent(self, limit: int = 20) -> list[dict[str, Any]]:
        traces = list(self._traces)[-limit:][::-1]
        return [t.to_dict() for t in traces]


_store: TraceStore | None = None


def get_trace_store() -> TraceStore:
    global _store
    if _store is None:
        _store = TraceStore()
    return _store


def new_trace_id() -> str:
    return uuid.uuid4().hex[:16]


def start_trace(query: str) -> Trace:
    """Create a new trace, set it as current, and return it."""
    trace = Trace(trace_id=new_trace_id(), query=query, created_at=time.time())
    _current_trace.set(trace)
    return trace


def get_current_trace() -> Trace | None:
    return _current_trace.get()


def set_attribute(key: str, value: Any) -> None:
    trace = _current_trace.get()
    if trace is not None:
        trace.attributes[key] = value


@contextmanager
def span(name: str, **attributes: Any) -> Iterator[Span]:
    """Record a timed span on the current trace (no-op if no trace is active)."""
    trace = _current_trace.get()
    current = Span(name=name, start_ms=time.perf_counter() * 1000, attributes=dict(attributes))
    if trace is not None:
        trace.spans.append(current)
    try:
        yield current
    except Exception as exc:
        current.status = "error"
        current.attributes.setdefault("error", str(exc))
        if trace is not None:
            trace.status = "error"
        raise
    finally:
        current.end_ms = time.perf_counter() * 1000


def finish_trace(trace: Trace, **attributes: Any) -> None:
    """Attach final attributes and persist the trace to the store."""
    trace.attributes.update(attributes)
    get_trace_store().add(trace)
    _current_trace.set(None)
