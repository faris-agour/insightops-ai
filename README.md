# InsightOps AI

InsightOps AI is a lightweight backend assistant for sales analytics. It uses rule-based intent routing (no LLM) with structured outputs from FastAPI.

## Overview

The API receives a user query at POST /analyze, classifies intent using simple matching rules, routes to the right sales tool, and returns a structured result plus a short insight.

## Current Implementation

InsightOps AI v2 is a rule-based multi-intent analytics backend for sales data. It classifies user queries, routes them to the appropriate tool, and returns structured results with short insights.

- Intent detection using keyword groups and pattern matching  
- Multi-intent routing (report, status, product insights, regional comparison)  
- Modular tool-based architecture (separate functions per task)  
- Data analysis using pandas on structured datasets  
- Structured JSON responses with short rule-based insights  
- Deterministic and testable design, ready for future LLM integration

## Key Features

- Multi-intent sales query classification
- Structured analytics responses
- Rule-based insights per intent
- FastAPI endpoint for easy testing in Swagger
- Unit-tested behavior


## Architecture

```
POST /analyze (query)
    ↓
Intent Classifier (rule-based)
    ↓
Task Router
    ↓
Sales Tool Function
    ↓
Structured Result + Insight
```

**Layers:**
- API layer: `app/main.py`
- Agent layer: `app/agents/simple_agent.py`
- Tool layer: `app/tools/sales_tools.py`

## Website Request Bodies and Responses

### 1. Sales Report

Request body:

```json
{ "query": "sales report" }
```

Response body:

```json
{
  "task": "sales_report",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "top_product": "Analytics Pack",
    "worst_product": "Reporting Add-on"
  },
  "insight": "Sales report is ready. Analytics Pack is leading, while Reporting Add-on is trailing."
}
```

![sales report output](docs/screenshots/request-1-sales-report.svg)

### 2. Sales Status / Trend

Request body:

```json
{ "query": "how are sales doing this week?" }
```

Response body:

```json
{
  "task": "sales_status",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "trend": "stable",
    "daily_variation_pct": 22.05
  },
  "insight": "Sales are stable with moderate variation across days."
}
```

![sales status output](docs/screenshots/request-2-how-are-sales-doing.svg)

### 3. Compare Sales by Region

Request body:

```json
{ "query": "compare sales by region" }
```

Response body:

```json
{
  "task": "sales_by_region",
  "result": {
    "best_region": "East",
    "best_region_revenue": 250093.02,
    "worst_region": "South",
    "worst_region_revenue": 196046.47,
    "regions": [
      {
        "region": "East",
        "revenue": 250093.02
      },
      {
        "region": "North",
        "revenue": 244244.26
      },
      {
        "region": "South",
        "revenue": 196046.47
      }
    ]
  },
  "insight": "Region East has the highest sales."
}
```

![sales by region output](docs/screenshots/request-3-compare-sales-by-region.svg)

### 4. Worst Performing Product

Request body:

```json
{ "query": "what is the worst performing product?" }
```

Response body:

```json
{
  "task": "worst_product",
  "result": {
    "product": "Reporting Add-on",
    "revenue": 79795.15
  },
  "insight": "Reporting Add-on is underperforming compared to other products."
}
```

![worst product output](docs/screenshots/request-4-worst-performing-product.svg)

## Environment Setup

### Prerequisites

- Python 3.10+ (3.11 recommended)
- conda or compatible environment manager

### Create and Activate Environment

```bash
cd insightops-ai
conda env create -f environment.yml
conda activate insightops-ai
```

## Run API

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Open Swagger UI at http://127.0.0.1:8010/docs

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s tests -p "test_*.py" -v
```

## Project Structure

```
insightops-ai/
├── app/
│   ├── main.py
│   ├── agents/
│   │   └── simple_agent.py
│   ├── tools/
│   │   └── sales_tools.py
│   └── __init__.py
├── docs/
│   └── screenshots/
├── data/
│   ├── sales.csv
│   └── generate_sales_data.py
├── tests/
│   ├── test_agent_loop.py
│   └── README.md
├── environment.yml
├── GETTING_STARTED.md
└── README.md
```

## Documentation

- [GETTING_STARTED.md](GETTING_STARTED.md)
- [tests/README.md](tests/README.md)
