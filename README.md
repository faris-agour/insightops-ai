# InsightOps AI

InsightOps AI is an agentic sales analytics backend that turns natural-language business questions into structured, explainable answers.

It combines deterministic analytics from earlier versions with a resilient LLM decision layer, then adds production-focused features in v0.4 such as streaming, metrics, circuit breaker, caching, and stronger request validation.

## Overview

InsightOps AI processes analytics queries through a layered orchestration flow that:

- Classifies intent using LLM-first routing with deterministic fallback
- Executes specialized analytics tools on sales data
- Generates readable insights with summary, reasoning, and recommendation
- Tracks runtime health through metrics, logs, and history

## Version Snapshot

| Version | Focus | Key Additions |
|--------|-------|---------------|
| v0.2 | Foundation | Rule-based intent classification, 5 core sales tools, stable API responses |
| v0.3 | Intelligence | Multi-provider LLM layer, adaptive model selection, richer insight responses |
| v0.4 | Production Readiness | Anomaly detection, forecasting, trend analysis, SSE streaming, circuit breaker, metrics, cache, stricter validation |

## v0.2 Foundation

The v0.2 release established the reliable base:

- Rule-based intent classification using keyword and pattern signals
- Deterministic analytics tools for sales reporting and product/region analysis
- Predictable response contract with task, result, and insight
- FastAPI API layer with baseline test coverage

## v0.3 Enhancements

v0.3 introduced the intelligence layer on top of v0.2:

- LLM-assisted intent decisioning with provider failover
- Adaptive model selection for simple vs complex queries
- Enhanced insight quality with summary + reasoning + recommendation
- Rule-based fallback remained active for high reliability

## v0.4 Enhancements

v0.4 moves the project from a strong prototype to a production-ready API baseline:

- New analytics intents:
  - anomaly_detection
  - forecast_revenue
  - trend_analysis
- Reliability and resilience:
  - provider circuit breaker
  - per-provider timeout strategy
  - deterministic fallback if LLM path fails
- Observability:
  - `/health`
  - `/metrics`
  - `/history`
  - structured request logging and token usage tracking
- Performance:
  - TTL cache for sales dataset loading
  - cache invalidation endpoint
- API hardening:
  - strict request validation and sanitization
  - safer exception handling and standardized responses
  - CORS support
- Real-time support:
  - SSE streaming endpoint `/analyze/stream`

## Why This API Stands Out

Compared to many analytics APIs, InsightOps AI provides:

- Natural-language routing instead of many rigid report-only endpoints
- LLM intelligence with strong fallback, not hard dependency on one model
- Explainable output, not just raw numbers
- Real-time streaming option for progressive user experience
- Built-in operational visibility (health, metrics, history)

## Current Architecture

```text
POST /analyze or /analyze/stream
        ↓
LLM Decision Layer (optional)
        ↓ success                  ↓ fail
 Provider + model routing      Rule-based classifier
        ↓                          ↓
          Task Router + Analytics Tools
                     ↓
       Structured Response + Insight
                     ↓
           Metrics + History + Logs
```

## Multi-Provider LLM Layer

The LLM decision layer supports a configurable provider chain:

1. Groq (primary)
2. Hugging Face (secondary)
3. Jetstream (tertiary)

Behavior details:

- Provider order controlled by `INSIGHTOPS_LLM_PROVIDER_ORDER`
- Circuit breaker skips unstable providers temporarily
- Each provider has its own timeout for better overall latency
- If all providers fail, deterministic rule-based routing handles the query

## Adaptive Model Selection

Model routing selects between fast and strong models based on query complexity.

- Fast model for short/simple intent detection
- Strong model for complex queries (forecasting, trend, deeper analysis)
- Thresholds and model names are configurable via environment variables

## Rich Insight Responses

Each final response includes:

- Summary: short business headline
- Reasoning: context behind the result
- Recommendation: practical next action

This makes the API more useful for stakeholders than plain numeric output alone.

## API Endpoints

| Method | Endpoint | Purpose |
|--------|----------|---------|
| GET | `/` | Service banner and version |
| GET | `/health` | Service/data/provider health snapshot |
| GET | `/metrics` | Counters, latency, tokens, cache, breaker state |
| GET | `/history` | Recent analyzed queries |
| POST | `/analyze` | Synchronous analysis response |
| POST | `/analyze/stream` | Streaming analysis via SSE |
| POST | `/admin/cache/invalidate` | Clear sales cache |

## Example Requests / Responses

### Sales Report

Request:

```json
{ "query": "sales report" }
```

Response (shape):

```json
{
  "task": "sales_report",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "top_product": "Analytics Pack",
    "worst_product": "Reporting Add-on"
  },
  "insight": "...",
  "model_used": "llama-3.1-8b-instant",
  "provider_used": "Groq",
  "latency_ms": 420.5,
  "api_version": "1.0"
}
```

### Forecast Revenue

Request:

```json
{ "query": "forecast next week revenue" }
```

Response (shape):

```json
{
  "task": "forecast_revenue",
  "result": {
    "forecast": [
      { "date": "2026-01-22", "predicted_revenue": 34407.87 }
    ],
    "trend_direction": "increasing"
  },
  "insight": "...",
  "model_used": "llama-3.3-70b-versatile"
}
```

### Stream Analysis (SSE)

```bash
curl -N -X POST http://127.0.0.1:8010/analyze/stream \
  -H "Content-Type: application/json" \
  -d '{"query":"show me anomalies"}'
```

## Environment Setup

### Prerequisites

- Python 3.11
- Conda (recommended)

### Installation

```bash
cd insightops-ai
conda env create -f environment.yml
conda activate insightops-ai
```

### Configuration

Create `.env` from the template:

PowerShell:

```powershell
Copy-Item .env.example .env
```

Then set your API keys:

- `GROQ_API_KEY`
- `HF_API_KEY`
- `JETSTREAM_API_KEY`

Recommended core settings:

```ini
INSIGHTOPS_LLM_ENABLED=true
INSIGHTOPS_LLM_PROVIDER_ORDER=groq,huggingface,jetstream
INSIGHTOPS_FAST_MODEL=llama-3.1-8b-instant
INSIGHTOPS_STRONG_MODEL=llama-3.3-70b-versatile
INSIGHTOPS_STRONG_MODEL_MIN_TOKENS=12
INSIGHTOPS_GROQ_TIMEOUT=4
INSIGHTOPS_HF_TIMEOUT=8
INSIGHTOPS_JETSTREAM_TIMEOUT=10
INSIGHTOPS_CB_FAILURE_THRESHOLD=3
INSIGHTOPS_CB_COOLDOWN_SECONDS=60
INSIGHTOPS_DATA_CACHE_TTL_SECONDS=300
```

### Run API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Swagger docs:

- http://127.0.0.1:8010/docs

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
```

Current baseline:

- 30 tests
- Coverage for agent loop, provider routing, tool contracts, and v0.4 features

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

## License

Internal project.
