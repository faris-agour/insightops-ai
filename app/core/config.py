import logging
import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)


def _env_str(name: str, default: str = "") -> str:
    value = os.getenv(name, default)
    return value.strip() if value else default


def _env_int(name: str, default: int) -> int:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        parsed = int(raw)
        if parsed <= 0:
            logger.warning("Invalid %s=%s (must be > 0). Using default %s", name, raw, default)
            return default
        return parsed
    except ValueError:
        logger.warning("Invalid %s=%s (not an int). Using default %s", name, raw, default)
        return default


def _env_float(name: str, default: float) -> float:
    raw = os.getenv(name, "").strip()
    if not raw:
        return default
    try:
        parsed = float(raw)
        if parsed <= 0:
            logger.warning("Invalid %s=%s (must be > 0). Using default %s", name, raw, default)
            return default
        return parsed
    except ValueError:
        logger.warning("Invalid %s=%s (not a float). Using default %s", name, raw, default)
        return default


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


class Settings:
    APP_NAME = "InsightOps AI"
    APP_VERSION = "0.4.0"

    PROJECT_ROOT = Path(__file__).resolve().parents[2]

    LOG_LEVEL = _env_str("INSIGHTOPS_LOG_LEVEL", "INFO").upper()

    SALES_DATA_PATH = Path(
        _env_str("INSIGHTOPS_SALES_DATA_PATH", str(PROJECT_ROOT / "data" / "sales.csv"))
    )

    DATA_CACHE_TTL_SECONDS = _env_int("INSIGHTOPS_DATA_CACHE_TTL_SECONDS", 300)

    LLM_ENABLED = _env_bool("INSIGHTOPS_LLM_ENABLED", default=False)
    LLM_TIMEOUT_SECONDS = _env_float("INSIGHTOPS_LLM_TIMEOUT_SECONDS", 5.0)
    LLM_PROVIDER_ORDER = _env_str("INSIGHTOPS_LLM_PROVIDER_ORDER", "groq,huggingface,jetstream")

    PROVIDER_TIMEOUTS = {
        "groq": _env_float("INSIGHTOPS_GROQ_TIMEOUT", 4.0),
        "huggingface": _env_float("INSIGHTOPS_HF_TIMEOUT", 8.0),
        "jetstream": _env_float("INSIGHTOPS_JETSTREAM_TIMEOUT", 10.0),
    }

    CIRCUIT_BREAKER_FAILURE_THRESHOLD = _env_int("INSIGHTOPS_CB_FAILURE_THRESHOLD", 3)
    CIRCUIT_BREAKER_COOLDOWN_SECONDS = _env_int("INSIGHTOPS_CB_COOLDOWN_SECONDS", 60)

    QUERY_MAX_LENGTH = _env_int("INSIGHTOPS_QUERY_MAX_LENGTH", 500)
    QUERY_HISTORY_SIZE = _env_int("INSIGHTOPS_QUERY_HISTORY_SIZE", 100)

    CORS_ALLOW_ORIGINS = _env_str("INSIGHTOPS_CORS_ORIGINS", "*")

    FAST_MODEL = _env_str("INSIGHTOPS_FAST_MODEL", "llama-3.1-8b-instant")
    STRONG_MODEL = _env_str("INSIGHTOPS_STRONG_MODEL", "llama-3.3-70b-versatile")
    STRONG_MODEL_MIN_TOKENS = _env_int("INSIGHTOPS_STRONG_MODEL_MIN_TOKENS", 12)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
