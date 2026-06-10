"""Shared pytest fixtures.

The test suite is hermetic: it must not depend on a developer's local ``.env`` or
make network calls. This autouse fixture forces the LLM layer offline so the
deterministic fallbacks (and the mock provider) drive behavior. Individual tests
that intend to exercise an LLM-enabled path opt back in explicitly.
"""

from __future__ import annotations

import pytest

from app.core.config import get_settings


@pytest.fixture(autouse=True)
def _offline_llm(monkeypatch: pytest.MonkeyPatch) -> None:
    settings = get_settings()
    monkeypatch.setattr(settings, "LLM_ENABLED", False, raising=False)
