# InsightOps AI

InsightOps AI is an agentic analytics backend that orchestrates multi-intent sales queries through an LLM-assisted decision layer. The system combines deterministic rule-based logic with optional AI-powered intent classification, providing structured business insights with explainable reasoning and actionable recommendations.

## Overview

InsightOps AI processes natural language queries about sales analytics, routing them through an intelligent orchestration system that:

- **Classifies intent** using either rule-based patterns or LLM-assisted analysis
- **Executes analytics** via specialized sales tools
- **Generates insights** with summary, reasoning, and recommendations
- **Ensures reliability** through automatic fallback mechanisms

The system supports 5 core sales intents: sales reports, status updates, top/worst product analysis, and regional comparisons.

## v0.2 Foundation

The v0.2 release established the core analytics foundation:

- **Rule-based intent classification** using keyword matching and pattern recognition
- **Deterministic sales analytics** with 5 specialized tools for revenue analysis
- **Structured API responses** with task, result, and basic insight fields
- **Production-ready FastAPI backend** with comprehensive unit testing

This foundation provided reliable, predictable analytics without external dependencies.

## v0.3 Enhancements

v0.3 introduces intelligent orchestration while preserving the v0.2 foundation:

- **LLM-assisted intent classification** with multi-provider support and automatic failover
- **Adaptive model selection** based on query complexity and token analysis
- **Rich insight generation** with structured summary, reasoning, and recommendations
- **Enhanced response metadata** including model usage tracking

The v0.2 rule-based system remains active as a fallback, ensuring reliability when LLM services are unavailable.

## Current Architecture

```
POST /analyze (query)
    ↓
LLM Decision Layer (optional)
  ↓ (success) → Intent Classification
  ↓ (failure) → Rule-Based Fallback
    ↓
Task Router → Sales Tool Execution
    ↓
Structured Response + Rich Insights
```

**Core Components:**
- **API Layer** (`app/main.py`): FastAPI endpoint with request validation
- **Agent Layer** (`app/agents/simple_agent.py`): Intent routing and insight generation
- **LLM Layer** (`app/agents/llm_decision.py`, `llm_providers.py`, `model_router.py`): Optional AI orchestration
- **Tool Layer** (`app/tools/sales_tools.py`): Deterministic analytics execution

## Multi-Provider LLM Layer

v0.3 supports three LLM providers in a configurable priority chain:

1. **Groq** (Primary) — Fast inference for real-time classification
2. **Hugging Face** (Secondary) — Hosted open-source models as backup
3. **Jetstream** (Tertiary) — GPT-OSS-120B fallback inference service

**Provider Features:**
- Automatic failover on timeout or API errors
- Configurable provider ordering via `INSIGHTOPS_LLM_PROVIDER_ORDER`
- Individual provider enable/disable through environment variables
- Timeout handling with 5-second default limits

## Adaptive Model Selection

Model routing optimizes for query complexity:

- **Fast models** (e.g., `gpt-4o-mini`, `llama-3.1-8b-instant`) for simple queries
- **Strong models** (e.g., `gpt-4.1`, `llama-3.3-70b-versatile`) for complex analysis
- **Complexity detection** via token counting and keyword matching
- **Configurable thresholds** through environment variables

## Rich Insight Responses

Each response includes structured insights with three components:

- **Summary**: Concise headline finding
- **Reasoning**: Business context and significance
- **Recommendation**: Specific actionable next step

Insights are generated for all 5 intents, providing explainable AI responses that support business decision-making.

## Example Requests / Responses

### Sales Report

**Request:**
```json
{ "query": "sales report" }
```

**Response:**
```json
{
  "task": "sales_report",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "top_product": "Analytics Pack",
    "worst_product": "Reporting Add-on"
  },
  "insight": "Analytics Pack leads the portfolio while Reporting Add-on underperforms.\n\nWith $690,383.75 in total revenue and $32,875.42 daily average, the portfolio concentration on top performers indicates opportunity to optimize underperformers.\n\nConsider strategies to boost Reporting Add-on's performance, such as improved marketing, pricing adjustments, or feature enhancements.",
  "model_used": "llama-3.1-8b-instant"
}
```

### Sales Status

**Request:**
```json
{ "query": "how are sales doing?" }
```

**Response:**
```json
{
  "task": "sales_status",
  "result": {
    "total_revenue": 690383.75,
    "average_daily_revenue": 32875.42,
    "trend": "stable",
    "daily_variation_pct": 22.05,
    "daily_change_percent": -3.81
  },
  "insight": "Sales performance is holding steady with minor daily fluctuations.\n\nThe relatively stable trend (daily change: -3.8%) suggests a balanced market environment without major disruptive factors.\n\nFocus on incremental improvements to product offerings, customer retention, and operational efficiency.",
  "model_used": "llama-3.1-8b-instant"
}
```

### Top Product Analysis

**Request:**
```json
{ "query": "which product is selling the most?" }
```

**Response:**
```json
{
  "task": "top_product",
  "result": {
    "product": "Analytics Pack",
    "revenue": 217795.25,
    "percent_of_total_revenue": 31.5
  },
  "insight": "Analytics Pack is the top revenue generator in the portfolio.\n\nWith $217,795.25 in revenue (31.5% of total), Analytics Pack represents the strongest market segment and customer preference alignment.\n\nMaintain investment in Analytics Pack while leveraging its success to cross-sell and upsell complementary products to the same customer base.",
  "model_used": "llama-3.1-8b-instant"
}
```

### Regional Sales Comparison

**Request:**
```json
{ "query": "compare sales by region" }
```

**Response:**
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
  "insight": "Regional sales performance varies, with East leading the way.\n\nEast generated $250,093.02, representing the strongest regional execution. Geographic analysis reveals expansion opportunities in underperforming regions.\n\nAnalyze East's success factors and replicate them in lower-performing regions. Consider targeted regional campaigns and localized sales strategies.",
  "model_used": "llama-3.1-8b-instant"
}
```

### Worst Product Analysis

**Request:**
```json
{ "query": "what is the worst performing product?" }
```

**Response:**
```json
{
  "task": "worst_product",
  "result": {
    "product": "Reporting Add-on",
    "revenue": 79795.15,
    "percent_of_total_revenue": 11.6
  },
  "insight": "Reporting Add-on is underperforming relative to other offerings.\n\nAt $79,795.15 (11.6% of total revenue), Reporting Add-on shows weak market adoption. This may signal product-market fit issues, poor positioning, or insufficient customer awareness.\n\nEither reinvest in Reporting Add-on with targeted improvements and marketing, or consider discontinuing it to free resources for higher-performing products.",
  "model_used": "llama-3.1-8b-instant"
}
```

## Environment Setup

### Prerequisites

- Python 3.10+ (3.11 recommended)
- conda or compatible environment manager

### Installation

```bash
cd insightops-ai
conda env create -f environment.yml
conda activate insightops-ai
```

### Configuration

Copy `.env.example` to `.env` and configure the following:

#### Global Settings
```bash
INSIGHTOPS_LLM_ENABLED=true          # Enable LLM layer (default: false)
INSIGHTOPS_LLM_TIMEOUT_SECONDS=5     # Request timeout
INSIGHTOPS_LLM_PROVIDER_ORDER=groq,huggingface,jetstream  # Provider priority
```

#### Model Selection
```bash
INSIGHTOPS_FAST_MODEL=llama-3.1-8b-instant     # Simple queries
INSIGHTOPS_STRONG_MODEL=llama-3.3-70b-versatile # Complex queries
INSIGHTOPS_STRONG_MODEL_MIN_TOKENS=12          # Complexity threshold
```

#### Provider Configuration

**Groq (Primary):**
```bash
GROQ_API_KEY=your_groq_key_here
GROQ_API_URL=https://api.groq.com/openai/v1/chat/completions
```

**Hugging Face (Secondary):**
```bash
HF_API_KEY=your_huggingface_key_here
HF_API_URL=https://api-inference.huggingface.co/models
HF_MODEL=meta-llama/Llama-2-7b
```

**Jetstream (Tertiary):**
```bash
JETSTREAM_API_KEY=your_jetstream_key_here
JETSTREAM_API_URL=https://api.jetstream.ai/v1/chat/completions
JETSTREAM_MODEL=gpt-oss-120b
```

### API Server

```bash
uvicorn app.main:app --reload --host 127.0.0.1 --port 8010
```

Open Swagger UI at http://127.0.0.1:8010/docs

## Testing

```bash
python -m unittest discover -s tests -p "test_*.py"
python -m unittest discover -s tests -p "test_*.py" -v
```

The test suite covers:
- Rule-based intent classification (8 tests)
- LLM decision path and fallback (4 tests)
- Tool execution and data validation (4 tests)
- Provider configuration and routing (4 tests)

## Project Structure

```
insightops-ai/
├── app/
│   ├── main.py                    # FastAPI application
│   └── agents/
│       ├── simple_agent.py        # Intent routing & insights
│       ├── llm_decision.py        # LLM orchestration
│       ├── llm_providers.py       # Provider abstractions
│       └── model_router.py        # Adaptive model selection
│   └── tools/
│       └── sales_tools.py         # Analytics functions
├── data/
│   └── sales.csv                  # Sample dataset
├── tests/
│   └── test_agent_loop.py         # Unit tests
├── environment.yml                # Conda environment
├── .env.example                   # Configuration template
└── README.md                      # This file
```
