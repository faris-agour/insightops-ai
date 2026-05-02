# InsightOps AI

InsightOps AI is a lightweight foundation for an agentic data analyst system.
It is built to analyze structured data, explain insights, and support simple actions as the platform evolves.

## Key Idea

Agentic system that analyzes data, explains insights, and can take actions.

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

1. Create the conda environment.
2. Activate the environment.
3. Start the FastAPI app.

conda env create -f environment.yml
conda activate insightops-ai
uvicorn app.main:app --reload
