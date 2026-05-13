# InsightOps AI

InsightOps AI is a production-focused sales analytics API that combines deterministic analytics tools with LLM-powered intent routing.

It is designed to answer natural-language business questions with structured outputs, explainable insights, and resilient fallback behavior.

## At A Glance

| Item | Value |
|------|-------|
| Current version | v0.4.0 |
| API style | FastAPI REST + SSE streaming |
| Domain | Sales analytics |
| Routing strategy | LLM-first with deterministic fallback |
| LLM providers | Groq, Hugging Face, Jetstream |
| Reliability model | Circuit breaker + provider failover + rule fallback |
| Performance model | TTL cache on sales dataset |
| Observability | Metrics, structured logs, history, health checks |

## Why InsightOps AI Is Different

| Dimension | Typical Analytics API | InsightOps AI |
|-----------|------------------------|---------------|
| Query interface | Fixed endpoints per report | Natural-language entry point with multi-intent routing |
| LLM dependency | Single model or hard failure | Multi-provider fallback plus rule-based fallback |
| Explainability | Raw numbers only | Summary + reasoning + recommendation |
| Real-time UX | Request/response only | SSE streaming endpoint for progressive results |
| Reliability controls | Basic timeout only | Per-provider timeouts + circuit breaker |
| Performance | Recompute per request | Cached data loading (TTL cache) |
| Operations visibility | Minimal logs | Health, metrics, latency, token usage, query history |

## Version Evolution (What You Keep + What You Gain)

| Version | Main Goal | Key Features |
|---------|-----------|--------------|
| v0.2 | Deterministic foundation | Rule-based intent classification, 5 core tools, stable API responses |
| v0.3 | Intelligence layer | Multi-provider LLM routing, adaptive model selection, richer insights |
| v0.4 | Production hardening | Advanced analytics, SSE streaming, metrics, circuit breaker, caching, stricter validation |

All previous strengths remain available in v0.4.

## v0.4 Feature Set

| Category | Features |
|----------|----------|
| Advanced analytics | anomaly detection, revenue forecasting, trend analysis |
| Routing intelligence | LLM decision layer + adaptive fast/strong model selection |
| Resilience | Provider failover, per-provider timeout, circuit breaker, rule fallback |
| API hardening | Request sanitization, validation, safer error handling, CORS |
| Observability | `/health`, `/metrics`, `/history`, structured logging, token tracking |
| Performance | Sales data TTL cache + cache invalidation endpoint |
| Real-time | `/analyze/stream` using Server-Sent Events |

## Supported Intents

| Intent | Tool | Added In |
|--------|------|----------|
| sales_report | get_sales_summary | v0.2 |
| sales_status | get_sales_status | v0.2 |
| top_product | get_top_product | v0.2 |
| worst_product | get_worst_product | v0.2 |
| sales_by_region | get_sales_by_region | v0.2 |
| anomaly_detection | detect_anomalies | v0.4 |
| forecast_revenue | forecast_revenue | v0.4 |
| trend_analysis | analyze_trend | v0.4 |
| unknown | none | v0.2 |

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Service info and docs path |
| GET | `/health` | Health status for data source and provider availability |
| GET | `/metrics` | Runtime counters, latencies, tokens, cache stats, circuit breaker state |
| GET | `/history` | Recent query history with task and latency |
| POST | `/analyze` | Synchronous analysis |
| POST | `/analyze/stream` | Streaming analysis over SSE |
| POST | `/admin/cache/invalidate` | Invalidate sales data cache |

## High-Level Request Flow

1. Client sends query to `/analyze` or `/analyze/stream`.
2. Decision layer attempts LLM intent classification.
3. If LLM path fails, classifier falls back to deterministic rules.
4. Matching analytics tool executes.
5. API returns structured result plus insight text.
6. Metrics and query history are updated.

## Quick Start

### 1) Environment

```bash
cd insightops-ai
conda env create -f environment.yml
conda activate insightops-ai
```

### 2) Configure `.env`

```bash
cp .env.example .env
```

Set your provider keys in `.env`:

- `GROQ_API_KEY`
- `HF_API_KEY`
- `JETSTREAM_API_KEY`

### 3) Run

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Open docs at: `http://127.0.0.1:8010/docs`

## Important Configuration

| Variable | Example | Purpose |
|----------|---------|---------|
| INSIGHTOPS_LLM_ENABLED | true | Enable/disable LLM decision layer |
| INSIGHTOPS_LLM_PROVIDER_ORDER | groq,huggingface,jetstream | Provider priority order |
| INSIGHTOPS_FAST_MODEL | llama-3.1-8b-instant | Model for simple queries |
| INSIGHTOPS_STRONG_MODEL | llama-3.3-70b-versatile | Model for complex queries |
| INSIGHTOPS_STRONG_MODEL_MIN_TOKENS | 12 | Token threshold for strong model |
| INSIGHTOPS_GROQ_TIMEOUT | 4 | Groq timeout in seconds |
| INSIGHTOPS_HF_TIMEOUT | 8 | Hugging Face timeout in seconds |
| INSIGHTOPS_JETSTREAM_TIMEOUT | 10 | Jetstream timeout in seconds |
| INSIGHTOPS_CB_FAILURE_THRESHOLD | 3 | Circuit breaker failure threshold |
| INSIGHTOPS_CB_COOLDOWN_SECONDS | 60 | Circuit breaker cooldown period |
| INSIGHTOPS_DATA_CACHE_TTL_SECONDS | 300 | Sales data cache TTL |
| INSIGHTOPS_QUERY_MAX_LENGTH | 500 | Max query length |
| INSIGHTOPS_QUERY_HISTORY_SIZE | 100 | Max in-memory query history |

## Example API Calls

### Analyze (sync)

```bash
curl -X POST http://127.0.0.1:8010/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"forecast next week revenue"}'
```

### Analyze (stream)

```bash
curl -N -X POST http://127.0.0.1:8010/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"show me anomalies"}'
```

### Health + Metrics

```bash
curl http://127.0.0.1:8010/health
curl http://127.0.0.1:8010/metrics
```

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
```

| Coverage Area | Status |
|---------------|--------|
| Core agent loop and fallback behavior | covered |
| LLM orchestration and provider ordering | covered |
| Sales tools output contracts | covered |
| v0.4 analytics, cache, breaker, metrics, history | covered |

Baseline: 30 tests.

## Project Structure

```text
insightops-ai/
├── app/
│   ├── main.py
│   ├── schemas.py
│   ├── core/
│   │   ├── config.py
│   │   ├── logging_config.py
│   │   ├── cache.py
│   │   ├── circuit_breaker.py
│   │   └── metrics.py
│   ├── agents/
│   │   ├── simple_agent.py
│   │   ├── llm_decision.py
│   │   ├── llm_providers.py
│   │   └── model_router.py
│   ├── analysis/
│   │   └── advanced_analytics.py
│   ├── services/
│   │   └── query_history.py
│   └── tools/
│       └── sales_tools.py
├── data/
│   ├── sales.csv
│   └── generate_sales_data.py
├── tests/
│   ├── test_agent_loop.py
│   └── test_v04_features.py
├── environment.yml
├── .env.example
├── GETTING_STARTED.md
└── README.md
```

## Enterprise Next Steps

- Add authentication and authorization.
- Add rate limiting.
- Add persistent storage (for history and reporting).
- Add distributed cache (Redis) for scale-out deployments.
- Add Prometheus/Grafana integration.
- Add CI/CD deployment hardening.

## License

Internal project.
