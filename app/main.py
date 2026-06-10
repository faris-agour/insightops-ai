import asyncio
import json
import time

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, PlainTextResponse, StreamingResponse

from app.agents.llm_decision import get_circuit_breaker_state
from app.agents.llm_providers import get_providers_in_order
from app.agents.prompts import get_prompt_registry
from app.agents.simple_agent import run_agent
from app.core.config import get_settings
from app.core.logging_config import configure_logging, get_logger
from app.core.metrics import get_metrics
from app.core.tracing import get_trace_store
from app.schemas import AnalyzeRequest, AnalyzeResponse, HealthStatus
from app.services.query_history import get_history
from app.tools.sales_tools import get_cache_stats, invalidate_sales_cache, load_sales_data

settings = get_settings()
configure_logging(settings.LOG_LEVEL, json_logs=settings.JSON_LOGS)
logger = get_logger(__name__)

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LLM-assisted sales analytics with multi-provider routing, anomaly detection, and forecasting.",
)

cors_origins = (
    [origin.strip() for origin in settings.CORS_ALLOW_ORIGINS.split(",") if origin.strip()]
    if settings.CORS_ALLOW_ORIGINS
    else ["*"]
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

_metrics = get_metrics()
_history = get_history()


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.perf_counter()
    response = await call_next(request)
    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        "%s %s -> %d (%.1fms)",
        request.method, request.url.path, response.status_code, duration_ms,
    )
    return response


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s: %s", request.url.path, exc)
    _metrics.increment("errors.unhandled")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "path": str(request.url.path)},
    )


@app.get("/")
def read_root() -> dict[str, str]:
    return {
        "message": f"{settings.APP_NAME} is running",
        "version": settings.APP_VERSION,
        "docs": "/docs",
    }


@app.get("/health", response_model=HealthStatus)
def health() -> HealthStatus:
    data_source_ok = True
    try:
        df = load_sales_data()
        data_source_ok = not df.empty
    except Exception as exc:
        logger.warning("Health check data source failed: %s", exc)
        data_source_ok = False

    available_providers = [
        provider.get_name()
        for provider in get_providers_in_order()
        if provider.is_configured()
    ]

    if not data_source_ok:
        status = "error"
    elif settings.LLM_ENABLED and not available_providers:
        status = "degraded"
    else:
        status = "ok"

    return HealthStatus(
        status=status,
        version=settings.APP_VERSION,
        data_source_ok=data_source_ok,
        llm_enabled=settings.LLM_ENABLED,
        providers_available=available_providers,
        uptime_seconds=_metrics.snapshot()["uptime_seconds"],
    )


@app.get("/metrics")
def metrics() -> dict[str, object]:
    snapshot = _metrics.snapshot()
    snapshot["cache"] = get_cache_stats()
    snapshot["circuit_breaker"] = get_circuit_breaker_state()
    return snapshot


@app.get("/metrics/prometheus")
def metrics_prometheus() -> PlainTextResponse:
    return PlainTextResponse(_metrics.prometheus(), media_type="text/plain; version=0.0.4")


@app.get("/traces")
def traces(limit: int = 20) -> dict[str, object]:
    limit = max(1, min(limit, 100))
    return {"traces": get_trace_store().recent(limit=limit)}


@app.get("/traces/{trace_id}")
def trace_detail(trace_id: str) -> dict[str, object]:
    trace = get_trace_store().get(trace_id)
    if trace is None:
        raise HTTPException(status_code=404, detail="trace not found")
    return trace.to_dict()


@app.get("/prompts")
def prompts() -> dict[str, object]:
    return {"prompts": get_prompt_registry().list_ids()}


@app.get("/history")
def history(limit: int = 20) -> dict[str, object]:
    limit = max(1, min(limit, 100))
    return {"entries": _history.list(limit=limit)}


@app.post("/admin/cache/invalidate")
def invalidate_cache() -> dict[str, str]:
    invalidate_sales_cache()
    return {"status": "ok", "message": "sales data cache invalidated"}


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    try:
        result = run_agent(request.query)
    except FileNotFoundError as exc:
        logger.error("Sales data missing: %s", exc)
        raise HTTPException(status_code=503, detail="Sales data source unavailable") from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    response = AnalyzeResponse(
        task=str(result.get("task", "unknown")),
        result=result.get("result", {}) or {},
        insight=str(result.get("insight", "")),
        model_used=str(result.get("model_used", "rule-based-fallback")),
        provider_used=result.get("provider_used"),
        latency_ms=float(result.get("latency_ms", 0.0)),
        trace_id=result.get("trace_id"),
        tokens=int(result.get("tokens", 0) or 0),
        cost_usd=float(result.get("cost_usd", 0.0) or 0.0),
    )
    _history.add(
        query=request.query,
        task=response.task,
        model_used=response.model_used,
        latency_ms=response.latency_ms,
    )
    return response


@app.post("/analyze/stream")
async def analyze_stream(request: AnalyzeRequest):
    async def event_generator():
        yield _sse_event("start", {"query": request.query})
        await asyncio.sleep(0)

        loop = asyncio.get_event_loop()
        try:
            result = await loop.run_in_executor(None, run_agent, request.query)
        except Exception as exc:
            yield _sse_event("error", {"detail": str(exc)})
            return

        yield _sse_event(
            "decision",
            {
                "task": result.get("task"),
                "model_used": result.get("model_used"),
                "provider_used": result.get("provider_used"),
            },
        )
        yield _sse_event("result", {"result": result.get("result", {})})

        insight = str(result.get("insight", ""))
        for chunk in _chunk_text(insight, size=80):
            yield _sse_event("insight_chunk", {"text": chunk})
            await asyncio.sleep(0.05)

        yield _sse_event(
            "complete",
            {
                "latency_ms": result.get("latency_ms"),
                "task": result.get("task"),
            },
        )

        _history.add(
            query=request.query,
            task=str(result.get("task", "unknown")),
            model_used=str(result.get("model_used", "rule-based-fallback")),
            latency_ms=float(result.get("latency_ms", 0.0)),
        )

    return StreamingResponse(event_generator(), media_type="text/event-stream")


def _sse_event(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


def _chunk_text(text: str, size: int) -> list[str]:
    if not text:
        return []
    return [text[i : i + size] for i in range(0, len(text), size)]
