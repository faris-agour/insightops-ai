# Contributing to InsightOps AI

Thanks for your interest in improving InsightOps AI! This guide gets you productive fast.

## Development setup

```bash
git clone https://github.com/farisabouagour/insightops-ai.git
cd insightops-ai
pip install -r requirements-dev.txt
pip install -e .
pre-commit install   # optional but recommended
```

The project runs fully offline thanks to the deterministic **mock LLM provider** — no API
keys are required to develop or run the test suite.

## Quality gate

Every change must pass the same gate CI runs. Run it locally with:

```bash
make check        # ruff + mypy + pytest + eval
# or individually:
make lint         # ruff check
make format       # ruff format + autofix
make type         # mypy
make test         # pytest
make eval         # intent-classification accuracy gate
```

- **Lint/format**: [ruff](https://docs.astral.sh/ruff/) (config in `pyproject.toml`).
- **Types**: [mypy](https://mypy.readthedocs.io/) over `app/`.
- **Tests**: [pytest](https://docs.pytest.org/); tests are hermetic (no network).
- **Eval**: `python -m app.eval.run` must stay at or above the accuracy threshold.

## Conventions

- Follow [Conventional Commits](https://www.conventionalcommits.org/) (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- Keep prompts in `app/agents/prompts.py` (versioned), never inline.
- Add a golden case to `app/eval/dataset.py` whenever you find a misclassification.
- New endpoints get a Pydantic response model and a test.

## Pull requests

1. Branch from `main` (`feat/...`, `fix/...`).
2. Make the change + add tests.
3. Ensure `make check` is green.
4. Open a PR describing the change and the rationale.

By contributing you agree your work is licensed under the project's [MIT License](LICENSE).
