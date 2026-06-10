# InsightOps AI — v0.5 Roadmap: "Agentic Intelligence & LLMOps Platform"

> Goal: elevate InsightOps AI from a strong production API baseline (v0.4) into a
> portfolio-grade, world-class **agentic analytics platform** with first-class
> LLMOps, observability, production infrastructure, and a live demo dashboard.

This roadmap is organized into 4 pillars + a polish pass. Each pillar is shippable
independently, so progress is visible at every step.

---

## Pillar 1 — Agentic Depth (Multi-Agent Consensus)

Turn the planned consensus architecture into a real, LLM-backed multi-agent system.

- **`app/agents/base.py`** — `Agent` abstraction: `name`, `role`, `analyze(context) -> AgentFinding`.
- **Specialized agents** (each combines a deterministic tool + an LLM "perspective" prompt):
  - `TrendAnalystAgent` → uses `analyze_trend`
  - `RiskAssessorAgent` → uses `detect_anomalies`
  - `ForecastingSpecialistAgent` → uses `forecast_revenue`
- **`ConsensusWorkspace`** — shared structure collecting `AgentFinding`s with confidence.
- **`ReconcilerAgent`** — LLM-backed judge that synthesizes findings, flags conflicts,
  and produces a final reconciled insight + an overall confidence score.
- **`AgentOrchestrator`** — runs specialized agents concurrently, then reconciles.
- **New endpoint** `POST /analyze/consensus` → returns each agent's finding + reconciled output.
- Mock-friendly: every agent works offline via deterministic tools + mock LLM fallback.

## Pillar 2 — LLMOps & Observability

The features that signal real "LLMOps" maturity to reviewers.

- **Tracing** (`app/core/tracing.py`): per-request `trace_id`, spans for decision/tools/agents,
  attached to responses and logs. `GET /traces/{trace_id}` + `GET /traces` (recent).
- **Eval harness** (`app/eval/`): golden dataset (query → expected intent), runner
  `python -m app.eval.run` producing an accuracy + confusion report; wired into CI.
- **Prompt registry** (`app/agents/prompts.py`): versioned, centralized prompts (no more inline strings).
- **Cost & token tracking**: per-provider pricing table → cost estimate in `/metrics`.
- **Guardrails** (`app/core/guardrails.py`): prompt-injection heuristics, output schema validation,
  basic PII redaction in logs.
- **Structured JSON logging** option (toggle via env) for log aggregation.
- **Prometheus endpoint** `GET /metrics/prometheus` (text exposition format).

## Pillar 3 — Production Infrastructure

Make it clone-and-run, CI-green, and container-ready.

- **`pyproject.toml`** — packaging + ruff + mypy + pytest config (single source of truth).
- **`requirements.txt` / `requirements-dev.txt`** — pip path alongside conda `environment.yml`.
- **`Dockerfile`** (slim, multi-stage) + **`docker-compose.yml`** + **`.dockerignore`**.
- **GitHub Actions** (`.github/workflows/ci.yml`): ruff → mypy → pytest (+coverage) → eval smoke.
- **`Makefile`** — `make install/run/test/lint/format/eval/docker`.
- **Pre-commit** (`.pre-commit-config.yaml`).
- **Repo hygiene**: `LICENSE` (MIT), `CONTRIBUTING.md`, `CHANGELOG.md`, `CODE_OF_CONDUCT.md`,
  issue/PR templates.
- **Test migration**: unittest → pytest, raise coverage, add consensus/guardrails/tracing tests.

## Pillar 4 — Demo UI / Dashboard

A zero-build, dependency-light dashboard served by FastAPI so anyone can try it instantly.

- **`app/static/`** — single-page dashboard (vanilla JS + Chart.js via CDN).
  - Natural-language query box → calls `/analyze`.
  - **Live streaming** view via `/analyze/stream` (SSE).
  - **Multi-agent consensus** view showing each agent + reconciled verdict.
  - **Live metrics** panel (latency, tokens, cost, provider health, circuit breaker).
  - Forecast/trend/anomaly charts.
- Mounted at `GET /` (or `/dashboard`), API banner moves to `/api`.

## Pillar 5 — Documentation & Polish

- Rewrite **README** for v0.5: badges (CI, license, python), hero diagram, feature matrix,
  architecture diagrams (mermaid), quickstart (pip / conda / docker), API table, screenshots/GIF.
- **`docs/ARCHITECTURE.md`** — deep dive (agentic flow, LLMOps, data flow).
- Bump version → `0.5.0`; update `CHANGELOG.md`.

---

## Suggested execution order

1. **Pillar 3 foundation** (pyproject, requirements, ruff/mypy, pytest migration) — sets quality bar.
2. **Pillar 2 core** (tracing, prompt registry, guardrails, cost) — infra the agents will use.
3. **Pillar 1** (multi-agent consensus) — the flagship feature, built on 2.
4. **Pillar 4** (dashboard) — visualizes 1+2.
5. **Pillar 3 CI/Docker** + **Pillar 5 docs** — wrap it as world-class.

Each pillar ends with green tests and a clean commit.
