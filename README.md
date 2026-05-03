# InsightOps AI

InsightOps AI is an early-stage agentic system designed to analyze structured data, generate actionable insights, and support decision-making workflows.

## Overview

Unlike traditional dashboards, InsightOps AI focuses on understanding data patterns and recommending actions based on analysis. The system employs a lightweight agent architecture that classifies user queries and routes them to appropriate analysis tools.

**Current Status:** Foundation phase with minimal agent loop implementation (6 passing tests).

## Key Features

- **Query Classification:** Simple intent-based task routing
- **Tool Integration:** Modular tool architecture for extensibility
- **Data Analysis:** Initial sales analytics capabilities
- **RESTful API:** FastAPI-based endpoint for query submission
- **Unit Tests:** Comprehensive test coverage (6/6 passing)

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
│   └── sales.csv              # Sample dataset
├── tests/
│   ├── test_agent_loop.py     # 6 unit tests
│   └── README.md              # Test documentation
├── environment.yml            # Conda dependencies
├── GETTING_STARTED.md         # Setup and running guide
└── README.md                  # This file
```

## Architecture

```
POST /analyze (query)
    ↓
Task Classifier (simple intent matching)
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

# Expected: Ran 6 tests in X.XXXs - OK
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
- **sales_analysis:** Computes total revenue from sales data
- **unknown:** Fallback for unrecognized queries

### Data Sources
- `data/sales.csv`: Sample sales dataset with date, product, region, revenue

### Response Format
```json
{
  "task": "sales_analysis",
  "result": {
    "total_revenue": 11960.0
  },
  "message": "Basic sales analysis completed"
}
```

## Testing

All tests pass: **6/6** ✅

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
