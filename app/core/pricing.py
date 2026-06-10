"""Token cost estimation for LLM usage tracking.

Maps model identifiers to blended USD-per-1K-token rates so ``/metrics`` can
surface an estimated spend alongside raw token counts. Rates are approximate and
configurable; the goal is to demonstrate cost-awareness, a core LLMOps concern,
not to bill anyone.
"""

from __future__ import annotations

# Approximate blended USD cost per 1K tokens (input+output averaged).
# Sources are provider public pricing; treated as estimates.
_PRICE_PER_1K: dict[str, float] = {
    "llama-3.1-8b-instant": 0.00010,
    "llama-3.3-70b-versatile": 0.00079,
    "llama-3.1-70b-versatile": 0.00079,
    "gpt-oss-120b": 0.00050,
    "mock-llm": 0.0,
    "rule-based-fallback": 0.0,
}

_DEFAULT_RATE = 0.0005


def rate_for(model: str) -> float:
    """Return the USD-per-1K-token rate for a model (default if unknown)."""
    return _PRICE_PER_1K.get(model, _DEFAULT_RATE)


def estimate_cost(model: str, total_tokens: int) -> float:
    """Estimate USD cost for ``total_tokens`` produced by ``model``."""
    if total_tokens <= 0:
        return 0.0
    return round((total_tokens / 1000.0) * rate_for(model), 6)
