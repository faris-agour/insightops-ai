# Getting Started

This guide gets InsightOps AI running locally in a couple of minutes. It runs **fully offline**
(no API keys) thanks to the built-in mock LLM provider.

## Prerequisites

- Python **3.11**
- pip, conda, **or** Docker

## 1. Install & run

### pip

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

### conda

```bash
conda env create -f environment.yml
conda activate insightops-ai
uvicorn app.main:app --reload --port 8010
```

### Docker

```bash
docker compose up --build
```

## 2. Open it

- 🎨 Dashboard → <http://127.0.0.1:8010/>
- 📚 Swagger → <http://127.0.0.1:8010/docs>
- 📊 Metrics → <http://127.0.0.1:8010/metrics>

## 3. Try the API

Single analysis:

```bash
curl -X POST http://127.0.0.1:8010/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"how are sales trending?"}'
```

Multi-agent consensus:

```bash
curl -X POST http://127.0.0.1:8010/analyze/consensus \
  -H "Content-Type: application/json" \
  -d '{"query":"what is the outlook and the risks?"}'
```

The response includes a `trace_id` — inspect the full span breakdown at
`GET /traces/{trace_id}`.

## 4. Enable real LLMs (optional)

```bash
cp .env.example .env        # PowerShell: Copy-Item .env.example .env
# then set in .env:
#   INSIGHTOPS_LLM_ENABLED=true
#   GROQ_API_KEY=...   (and/or HF_API_KEY / JETSTREAM_API_KEY)
```

With keys present, the decision layer and every agent upgrade from deterministic
narratives to real LLM reasoning. Without keys, the mock provider keeps everything working.

## 5. Development workflow

```bash
pip install -r requirements-dev.txt
make check        # ruff + mypy + pytest + eval (the full CI gate)
make test         # just the tests
make eval         # intent-classification accuracy report
make run          # dev server with reload
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for conventions and
[docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for the design deep-dive.

## Troubleshooting

- **Port already in use** → change `--port 8010` to another value.
- **Import errors** → run commands from the project root (`insightops-ai/`).
- **`uvicorn` not found** → `pip install -r requirements.txt` (or activate the conda env).
