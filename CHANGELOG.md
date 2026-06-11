# Changelog

All notable changes to this project are documented here. The format is based on
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and this project adheres to
[Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.5.0] - 2026-06-11

### Added — Agentic
- **Multi-agent collaborative consensus** (`POST /analyze/consensus`): three specialized
  agents (Trend Analyst, Risk Assessor, Forecasting Specialist) analyze independently,
  publish to a shared `ConsensusWorkspace`, and a **Reconciler** agent synthesizes a single
  verdict while surfacing optimism-vs-risk conflicts.
- `Agent` base abstraction with LLM-perspective generation and deterministic fallback.

### Added — LLMOps & Observability
- **Request tracing**: per-request `trace_id` with timed spans; `GET /traces`, `GET /traces/{id}`.
- **Versioned prompt registry** (`GET /prompts`) — prompts are artifacts, not inline strings.
- **Guardrails**: prompt-injection screening + PII redaction in logs.
- **Cost tracking**: per-model token cost estimation surfaced in `/metrics`.
- **Prometheus endpoint** `GET /metrics/prometheus`; p50/p95 latency; guardrail counters.
- **Structured JSON logging** (`INSIGHTOPS_JSON_LOGS`).
- **Offline mock LLM provider** so the full pipeline runs without API keys.
- **Eval harness**: golden dataset + scored runner (`python -m app.eval.run`), gated in CI.

### Added — Product & Infra
- **Interactive dashboard** (zero-build SPA) served at `/`: single analysis, multi-agent
  consensus, live SSE streaming, and an auto-refreshing observability panel with charts.
- `pyproject.toml`, `Dockerfile` (multi-stage, non-root), `docker-compose.yml`,
  **GitHub Actions CI** (ruff + mypy + pytest/coverage + eval + docker build), `Makefile`,
  pre-commit, MIT license, contributing guide.

### Changed
- JSON banner moved from `/` to `/api` (root now serves the dashboard).
- `AnalyzeResponse` now includes `trace_id`, `tokens`, and `cost_usd`.
- Version bumped to `0.5.0`.

## [0.4.0]
- Anomaly detection, revenue forecasting, trend analysis.
- Provider circuit breaker, per-provider timeouts, deterministic fallback.
- Observability: `/health`, `/metrics`, `/history`; TTL cache; SSE streaming; CORS; stricter validation.

## [0.3.0]
- Multi-provider LLM decision layer with failover and adaptive model selection.
- Richer insight responses (summary + reasoning + recommendation).

## [0.2.0]
- Rule-based intent classification, core sales tools, stable FastAPI response contract.
