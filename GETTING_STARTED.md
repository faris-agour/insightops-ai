# Getting Started

This guide explains how to set up and run InsightOps AI locally.

## Installation

### Prerequisites
- Python 3.10+ (3.11 recommended)
- conda or compatible package manager

### Step 1: Create Environment

Using conda:
```bash
cd insightops-ai
conda env create -f environment.yml
conda activate insightops-ai
```

If you encounter conda solver issues, use the classic solver:
```bash
conda config --set solver classic
conda env create -f environment.yml
```

Alternatively, use an existing environment (if available):
```bash
conda activate cliniq
```

### Step 2: Verify Installation

Run the tests to ensure everything is set up:
```bash
python -m unittest discover -s tests -p "test_*.py"
```

Expected output:
```
Ran 6 tests in 0.003s
OK
```

## Running the API

Start the FastAPI development server:
```bash
uvicorn app.main:app --reload
```

Server runs at: `http://127.0.0.1:8000`

### Test the Endpoint

#### Using curl
```bash
curl -X POST http://127.0.0.1:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"query":"analyze sales"}'
```

#### Using Python requests
```python
import requests

response = requests.post(
    "http://127.0.0.1:8000/analyze",
    json={"query": "analyze sales"}
)
print(response.json())
```

#### Expected Response
```json
{
  "task": "sales_analysis",
  "result": {
    "total_revenue": 11960.0
  },
  "message": "Basic sales analysis completed"
}
```

## API Endpoints

### GET /
Health check endpoint.
- Returns: `{"message": "InsightOps AI is running"}`

### POST /analyze
Main analysis endpoint. Classifies query intent and executes matching tool.
- Request body:
  ```json
  {
    "query": "string"
  }
  ```
- Response:
  ```json
  {
    "task": "string",
    "result": "object",
    "message": "string"
  }
  ```

## Project Structure

```
insightops-ai/
├── app/
│   ├── main.py                 # FastAPI entrypoint and endpoints
│   ├── agents/
│   │   └── simple_agent.py    # Task classifier and agent loop
│   ├── tools/
│   │   └── sales_tools.py     # Tool implementations
│   ├── analysis/              # Future analysis modules
│   ├── services/              # Future service integrations
│   └── __init__.py
├── data/
│   └── sales.csv              # Sample sales dataset
├── tests/
│   ├── test_agent_loop.py     # Unit tests
│   └── README.md              # Test documentation
├── environment.yml            # Conda dependencies
└── README.md                  # Project overview
```

## Development Workflow

1. Create or modify code in `app/` directories
2. Write tests in `tests/` directory
3. Run tests: `python -m unittest discover -s tests -p "test_*.py"`
4. Start dev server: `uvicorn app.main:app --reload`
5. Test endpoints with curl or Python client
6. Commit and push to GitHub

## Common Issues

### Conda Environment Not Found
```bash
conda config --set solver classic
conda env create -f environment.yml
```

### Module Import Errors
Ensure you're in the project root directory (`insightops-ai/`) before running commands.

### Port 8000 Already in Use
Run on a different port:
```bash
uvicorn app.main:app --reload --port 8001
```

## Next Steps

- Extend task classifier with more keywords
- Add new tool implementations in `app/tools/`
- Expand test coverage in `tests/`
- Integrate with external APIs in `app/services/`
