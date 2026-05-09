from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator


VALID_INTENTS = Literal[
    "sales_report",
    "sales_status",
    "top_product",
    "worst_product",
    "sales_by_region",
    "anomaly_detection",
    "forecast_revenue",
    "trend_analysis",
    "unknown",
]


class AnalyzeRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=500, description="Natural language sales query")

    @field_validator("query")
    @classmethod
    def sanitize_query(cls, value: str) -> str:
        cleaned = "".join(c for c in value if ord(c) >= 32 or c in "\n\t")
        cleaned = cleaned.strip()
        if not cleaned:
            raise ValueError("query must not be empty after sanitization")
        return cleaned


class AnalyzeResponse(BaseModel):
    task: str
    result: dict[str, Any]
    insight: str
    model_used: str
    provider_used: str | None = None
    latency_ms: float
    cached: bool = False
    api_version: str = "1.0"


class LLMDecisionPayload(BaseModel):
    intent: VALID_INTENTS
    reasoning: str = Field(default="Intent inferred from query context.", max_length=2000)
    suggested_tool: str = ""


class HealthStatus(BaseModel):
    status: Literal["ok", "degraded", "error"]
    version: str
    data_source_ok: bool
    llm_enabled: bool
    providers_available: list[str]
    uptime_seconds: float


class HistoryEntry(BaseModel):
    query: str
    task: str
    model_used: str
    latency_ms: float
    timestamp: float
