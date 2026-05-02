from fastapi import FastAPI


app = FastAPI(title="InsightOps AI", version="0.1.0")


@app.get("/")
def read_root() -> dict[str, str]:
    return {"message": "InsightOps AI is running"}
