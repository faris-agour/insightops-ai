# InsightOps AI

InsightOps AI is an early-stage agentic system designed to analyze business data, generate insights, and assist in decision-making workflows.

## Key Idea

Unlike traditional dashboards, InsightOps AI focuses on explaining why changes happen and suggesting what to do next.
## Early Scope

- Minimal API entrypoint for future orchestration
- Clean module layout for agents, analysis, services, and tools
- Simple local environment setup
- Extensible structure without over-engineering

## Architecture (High Level)

The FastAPI app is the entrypoint and will coordinate future system flows.
Analysis logic belongs in the analysis layer, external integrations in services, and reusable helper functions in tools.
Agent workflows will be added gradually in the agents layer as requirements become clear.

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
