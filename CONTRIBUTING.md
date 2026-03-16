# Contributing to Document RAG 🤝

Contributions are welcome. This document gives a short overview of how to get started.

## Getting started 🚀

- **Quick Start (Docker):** See the [README](README.md#quick-start) for running the full stack with `make up`, `make llm`, and `make frontend`.
- **Local development:** For running services on your host with only Qdrant in Docker, follow [docs/local-development.md](docs/local-development.md).
- **Configuration:** Copy the repo-wide env template with `cp .env.example .env` if you need to override defaults such as `LLM_URL` or feature toggles.

## Linting ✅

From the project root, run **`make lint`** to lint both the backend (Ruff) and frontend (ESLint). Install backend dev deps first: `pip install -r backend/requirements-dev.txt` (in the backend venv). See [docs/local-development.md](docs/local-development.md#linting) for `make lint-backend`, `make lint-frontend`, and `make format`.

## Running tests 🧪

From the project root, run **`make test`** to run backend, gateway, and MCP tests. See the [README](README.md#development) and Makefile for `make test-backend`, `make test-gateway`, and `make test-mcp`. Tests use `backend/shared` and the embedding service backend. Integration tests that require Qdrant are skipped by default (run them manually when Qdrant is available).

## Submitting changes 📬

The default branch is **`main`**. Open an issue to discuss larger changes, or send a pull request targeting `main`. For PRs, briefly describe the change and link any related issue if applicable.
