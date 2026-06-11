.PHONY: help install dev run test cov lint format type eval docker docker-up clean

help:  ## Show this help
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-14s\033[0m %s\n", $$1, $$2}'

install:  ## Install runtime dependencies
	pip install -r requirements.txt

dev:  ## Install dev dependencies + the package (editable)
	pip install -r requirements-dev.txt && pip install -e .

run:  ## Run the API + dashboard locally
	uvicorn app.main:app --reload --host 127.0.0.1 --port 8010

test:  ## Run the test suite
	pytest

cov:  ## Run tests with coverage
	pytest --cov=app --cov-report=term-missing

lint:  ## Lint with ruff
	ruff check app tests

format:  ## Auto-format with ruff
	ruff format app tests && ruff check --fix app tests

type:  ## Type-check with mypy
	mypy app

eval:  ## Run the intent-classification eval harness
	python -m app.eval.run

check: lint type test eval  ## Run the full quality gate

docker:  ## Build the Docker image
	docker build -t insightops-ai:0.5.0 .

docker-up:  ## Run via docker-compose
	docker compose up --build

clean:  ## Remove caches and build artifacts
	rm -rf .pytest_cache .mypy_cache .ruff_cache htmlcov .coverage coverage.xml dist build *.egg-info
