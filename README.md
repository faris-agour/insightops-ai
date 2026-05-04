# InsightOps AI

InsightOps AI is an early-stage agentic system designed to analyze structured data, generate actionable insights, and support decision-making workflows.

## Overview

Unlike traditional dashboards, InsightOps AI focuses on understanding data patterns and recommending actions based on analysis. The system employs a lightweight agent architecture that classifies user queries and routes them to appropriate analysis tools.

**Current Status:** v0.2 foundation with enhanced sales analysis and lightweight insight generation.

## Key Features

- **Query Classification:** Rule-based intent detection with flexible phrasing support
- **Tool Integration:** Modular tool architecture for extensibility
- **Data Analysis:** Sales metrics including total revenue, average daily revenue, and product ranking
- **Insight Generation:** Rule-based short insight message from computed metrics
- **RESTful API:** FastAPI-based endpoint for query submission
- **Unit Tests:** Comprehensive test coverage (7/7 passing)

## Project Structure

```
insightops-ai/
├── app/
│   ├── main.py                # FastAPI entrypoint
│   ├── agents/
│   │   └── simple_agent.py    # Task classifier, agent loop
│   ├── tools/
│   │   └── sales_tools.py     # Sales analysis tool
│   ├── analysis/              # Future: complex analysis modules
│   ├── services/              # Future: external integrations
│   └── __init__.py
├── data/
│   ├── sales.csv              # Realistic synthetic sales dataset
│   └── generate_sales_data.py # Dataset generator with anomalies
├── tests/
│   ├── test_agent_loop.py     # 7 unit tests
│   └── README.md              # Test documentation
├── environment.yml            # Conda dependencies
├── GETTING_STARTED.md         # Setup and running guide
└── README.md                  # This file
```

## Architecture

```
POST /analyze (query)
    ↓
Task Classifier (rule-based intent detection)
    ↓
Tool Router (execute matching tool)
    ↓
Result Aggregator (structured response)
```

**Layers:**
- **API Layer** (`app/main.py`): FastAPI entrypoint and endpoints
- **Agent Layer** (`app/agents/`): Task classification and orchestration
- **Tool Layer** (`app/tools/`): Tool implementations (sales, future)
- **Analysis Layer** (`app/analysis/`): Future complex analysis
- **Services Layer** (`app/services/`): Future external integrations

## Tech Stack

- **Runtime:** Python 3.11
- **Framework:** FastAPI + Uvicorn
- **Data:** Pandas, NumPy
- **Configuration:** python-dotenv
- **HTTP:** requests
- **Testing:** unittest

## Quick Start

### Prerequisites
- Python 3.10+ (3.11 recommended)
- conda or compatible environment manager

### Installation

```bash
# Clone or navigate to the repository
cd insightops-ai

# Create environment
conda env create -f environment.yml
conda activate insightops-ai

# Run tests (verify setup)
python -m unittest discover -s tests -p "test_*.py"

# Expected: Ran 7 tests in X.XXXs - OK
```

### Run the API

```bash
# Start development server
uvicorn app.main:app --reload
```

Server available at: `http://127.0.0.1:8000`

### Test the Endpoint

```bash
# Health check
curl http://127.0.0.1:8000/

# Analyze query
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"analyze sales"}'
```

## Current Capabilities

### Task Types
- **sales_analysis:** Computes revenue metrics and returns a short insight summary
- **unknown:** Fallback for unrecognized queries

### Data Sources
- `data/sales.csv`: Realistic synthetic dataset with date, product, region, channel, units_sold, revenue, cost
- `data/generate_sales_data.py`: Dataset generator script with anomaly scenarios

### Response Format
```json
{
  "task": "sales_analysis",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "top_product": "Analytics Pack",
    "worst_product": "Reporting Add-on"
  },
  "insight": "Sales are stable overall with Analytics Pack leading performance, while Reporting Add-on shows weaker results."
}
```

## Testing

All tests pass: **7/7** ✅

```bash
# Run all tests
python -m unittest discover -s tests -p "test_*.py"

# With verbose output
python -m unittest discover -s tests -p "test_*.py" -v

# Run single test
python -m unittest tests.test_agent_loop.TestAgentLoop.test_run_agent_sales
```

See [tests/README.md](tests/README.md) for detailed test documentation.

## Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md) — Setup, running, and common issues
- [tests/README.md](tests/README.md) — Test overview and coverage

