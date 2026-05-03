# Tests

## Overview

This directory contains unit tests for the InsightOps AI agent loop implementation.
Tests verify the core functionality: task classification, tool execution, and API endpoints.

## Test File: `test_agent_loop.py`

Tests are organized into a single test class `TestAgentLoop` with six unit tests.

### Test Cases

#### 1. `test_classify_task_sales`
Verifies that the task classifier correctly identifies sales-related queries.
- Input: "Please analyze sales"
- Expected: task type = "sales_analysis"

#### 2. `test_classify_task_unknown`
Verifies fallback behavior for unrecognized queries.
- Input: "show trends for support tickets"
- Expected: task type = "unknown"

#### 3. `test_analyze_sales_total_revenue`
Verifies that the sales analysis tool correctly reads data and computes total revenue.
- Expected: total_revenue = 11960.0 (sum of sales.csv)

#### 4. `test_run_agent_sales`
Tests the complete agent loop with a sales query.
- Input: "sales summary"
- Verifies task classification, result computation, and status message

#### 5. `test_run_agent_unknown`
Tests agent graceful handling of unknown queries.
- Input: "check customer churn"
- Verifies task = "unknown" and empty result

#### 6. `test_analyze_endpoint`
Tests the POST /analyze FastAPI endpoint end-to-end.
- Input: AnalyzeRequest with query = "sales dashboard"
- Verifies endpoint returns correct task, result, and message

## Running Tests

### Run All Tests
```bash
python -m unittest discover -s tests -p "test_*.py"
```

### Run Tests with Verbose Output
```bash
python -m unittest discover -s tests -p "test_*.py" -v
```

### Run a Single Test
```bash
python -m unittest tests.test_agent_loop.TestAgentLoop.test_run_agent_sales
```

## Test Results

All tests should pass with output:
```
Ran 6 tests in X.XXXs
OK
```

## Test Coverage

Tests cover:
- Agent task classification logic
- Tool execution and data loading
- Agent loop orchestration
- API endpoint integration
- Fallback handling for unknown tasks

## Adding New Tests

When extending the agent system:

1. Add the test method to `TestAgentLoop` class
2. Follow naming convention: `test_<feature_name>`
3. Use `self.assertEqual()` for assertions
4. Run tests before pushing to main branch

Example:
```python
def test_new_feature(self) -> None:
    result = new_function("test_input")
    self.assertEqual(result["expected_key"], expected_value)
```
