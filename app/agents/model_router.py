import os
import re


DEFAULT_FAST_MODEL = "llama-3.1-8b-instant"
DEFAULT_STRONG_MODEL = "llama-3.3-70b-versatile"
DEFAULT_STRONG_MODEL_MIN_TOKENS = 12
DEFAULT_COMPLEXITY_KEYWORDS = {
    "compare",
    "comparison",
    "versus",
    "vs",
    "forecast",
    "explain",
    "reason",
    "why",
    "breakdown",
    "anomaly",
    "trend",
    "strategy",
}


def _tokenize(query: str) -> set[str]:
    cleaned = re.sub(r"[^a-z0-9\s]", " ", query.lower())
    cleaned = " ".join(cleaned.split())
    return set(cleaned.split())


def _get_env_int(name: str, default: int) -> int:
    value = os.getenv(name, "").strip()
    if not value:
        return default

    try:
        parsed = int(value)
    except ValueError:
        return default

    return parsed if parsed > 0 else default


def _first_non_empty(*values: str) -> str:
    for value in values:
        if value and value.strip():
            return value.strip()
    return ""


def select_model(query: str) -> str:
    fast_model = _first_non_empty(
        os.getenv("INSIGHTOPS_FAST_MODEL", ""),
        os.getenv("FAST_MODEL", ""),
        DEFAULT_FAST_MODEL,
    )
    strong_model = _first_non_empty(
        os.getenv("INSIGHTOPS_STRONG_MODEL", ""),
        os.getenv("STRONG_MODEL", ""),
        DEFAULT_STRONG_MODEL,
    )
    strong_model_min_tokens = _get_env_int(
        "INSIGHTOPS_STRONG_MODEL_MIN_TOKENS", DEFAULT_STRONG_MODEL_MIN_TOKENS
    )

    extra_keywords_raw = os.getenv("INSIGHTOPS_STRONG_MODEL_KEYWORDS", "")
    extra_keywords = {
        keyword.strip().lower()
        for keyword in extra_keywords_raw.split(",")
        if keyword.strip()
    }

    complexity_keywords = DEFAULT_COMPLEXITY_KEYWORDS.union(extra_keywords)
    tokens = _tokenize(query)

    if len(tokens) >= strong_model_min_tokens:
        return strong_model

    if any(token in complexity_keywords for token in tokens):
        return strong_model

    return fast_model
