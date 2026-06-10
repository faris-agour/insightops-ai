"""Generic JSON completion across real LLM providers.

The intent router uses :func:`decide_with_llm`; the multi-agent layer needs free-form
JSON generation (an agent perspective, a reconciled verdict). This helper reuses the
existing provider chain for that, deliberately **excluding** the deterministic Mock
provider so callers can cleanly fall back to their own offline logic when no real
provider is configured.
"""

from __future__ import annotations

import json
from typing import Any

from app.agents.llm_providers import get_providers_in_order
from app.agents.model_router import select_model
from app.core.config import get_settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)
_settings = get_settings()


def _extract_json(raw: str) -> dict[str, Any] | None:
    raw = (raw or "").strip()
    if not raw:
        return None
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        if start == -1:
            return None
        try:
            parsed, _ = json.JSONDecoder().raw_decode(raw[start:])
        except json.JSONDecodeError:
            return None
    return parsed if isinstance(parsed, dict) else None


def complete_json(system_prompt: str, user_content: str) -> dict[str, Any] | None:
    """Return a parsed JSON dict from the first working real provider, else None."""
    if not _settings.LLM_ENABLED:
        return None

    model = select_model(user_content)
    for provider in get_providers_in_order():
        if provider.get_name() == "Mock" or not provider.is_configured():
            continue
        key = provider.get_name().lower()
        timeout = _settings.PROVIDER_TIMEOUTS.get(key, _settings.LLM_TIMEOUT_SECONDS)
        try:
            response = provider.send_decision_request(user_content, system_prompt, model, timeout)
            data = _extract_json(str(response.get("content", "")))
            if data is not None:
                data.setdefault("_provider", provider.get_name())
                data.setdefault("_model", model)
                data.setdefault("_tokens", int(response.get("total_tokens", 0) or 0))
                return data
        except Exception as exc:  # noqa: BLE001 - providers raise varied errors
            logger.warning("Agent LLM call via %s failed: %s", provider.get_name(), exc)
            continue
    return None
