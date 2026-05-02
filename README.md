# InsightOps AI

InsightOps AI is an early-stage agentic system that analyzes business data, identifies root causes, and supports decision-making workflows.

## Key Idea

Unlike traditional dashboards, InsightOps AI focuses on explaining why changes happen and suggesting what actions to take.

## Early Scope

- Minimal API entrypoint with a first agent-like analyze endpoint
- Clean module layout for agents, analysis, services, and tools
- Simple local environment setup
- Extensible structure without over-engineering

## Architecture (High Level)

The FastAPI app serves as the system entrypoint and coordinates request handling.
Analysis logic is handled in the analysis layer, external integrations in services, and reusable utilities in tools.
A simple agent loop classifies user intent and routes execution to the appropriate tool.
This structure is designed to evolve into a full agentic loop capable of analyzing, deciding, and acting autonomously.

## Tech Stack

- Python 3.11
- FastAPI
- Uvicorn
- Pandas
- NumPy
- python-dotenv
- requests

## Setup

conda env create -f environment.yml
conda activate insightops-ai
uvicorn app.main:app --reload

## Current Capabilities
- Basic query classification
- Tool-based data analysis (sales example)
- Simple agent loop (decision + execution)
