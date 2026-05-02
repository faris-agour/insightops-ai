from fastapi import FastAPI
from pydantic import BaseModel

from app.agents.simple_agent import run_agent


app = FastAPI(title="InsightOps AI", version="0.1.0")


class AnalyzeRequest(BaseModel):
    query: str


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "InsightOps AI is running"}


@app.post("/analyze")
def analyze(request: AnalyzeRequest) -> dict[str, object]:
    return run_agent(request.query)
