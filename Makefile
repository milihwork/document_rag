# Document RAG — start services and dev targets
# Separated stack: gateway (8000), ingestion (8001), embedding (8002), retrieval (8003), rag (8004), qdrant (6333).
# Run "make" or "make help". For full stack: make up (Docker), then make llm (host), make frontend (host).

.PHONY: help up down down-vol build frontend llm init-llama qdrant start stop-local
.PHONY: run-gateway run-ingestion run-embedding run-retrieval run-rag run-ml run-backends run-mcp
.PHONY: test test-backend test-gateway test-mcp lint lint-backend lint-frontend format format-backend format-frontend

help:
	@echo "Document RAG — targets:"
	@echo "  make up       — start all services in Docker (gateway, ingestion, embedding, retrieval, rag, ml, qdrant)"
	@echo "  make down     — stop containers (keeps data)"
	@echo "  make down-vol — stop containers and remove volume (deletes vectors)"
	@echo "  make build    — rebuild all Docker service images"
	@echo "  make frontend — install deps and run Vite dev server"
	@echo "  make llm      — run LLM server on host (foreground; run after make up)"
	@echo "  make init-llama — clone and build llama.cpp once (needed for make llm)"
	@echo "  make qdrant   — start only Qdrant"
	@echo "  make start    — Docker stack + frontend (local); then run 'make llm' in another terminal"
	@echo "  make stop-local — stop local frontend/API (ports 8000, 5173)"
	@echo "  make run-gateway — run gateway only (Node, port 8000)"
	@echo "  make run-gateway run-ingestion run-embedding run-retrieval run-rag — run single service locally"
	@echo "  make run-ml      — run ML service only (port 8005)"
	@echo "  make run-backends — run the Backends in one terminal (ingestion, embedding, retrieval, rag, ml)"
	@echo "  make run-mcp     — run MCP server (stdio) for Cursor/Claude Desktop"
	@echo "  make test        — run backend, gateway, and MCP tests"
	@echo "  make test-backend — run backend Python tests (pytest)"
	@echo "  make test-gateway — run Gateway unit tests"
	@echo "  make test-mcp    — run MCP service unit tests"
	@echo "  make lint        — run backend (Ruff) and frontend (ESLint) linters"
	@echo "  make lint-backend — run Ruff in backend/"
	@echo "  make lint-frontend — run ESLint in frontend/"
	@echo "  make format       — format backend (Ruff) and fix frontend (ESLint --fix)"

up:
	docker compose up -d

down:
	docker compose down

down-vol:
	docker compose down -v

build:
	docker compose build

frontend:
	cd frontend && npm install && npm run dev

llm:
	./backend/scripts/run_llm.sh

init-llama:
	./backend/scripts/init_llama.sh

qdrant:
	docker compose up -d qdrant

start: up
	@echo "--- All services (Docker) are up. Start frontend and LLM. ---"
	@echo "Waiting for gateway at http://127.0.0.1:8000/health ..."
	@i=0; while [ $$i -lt 30 ]; do curl -s -o /dev/null http://127.0.0.1:8000/health 2>/dev/null && break; i=$$((i+1)); sleep 1; done
	@(cd frontend && npm run dev) &
	@sleep 3
	@echo ""
	@echo "In another terminal run:  make llm"
	@echo "Open the frontend URL (e.g. http://localhost:5173). Gateway is at http://localhost:8000"
	@echo ""

run-gateway:
	cd backend/services/gateway && npm install && npm run dev

run-ingestion:
	cd backend && PYTHONPATH=. ./venv/bin/uvicorn services.ingestion.app.main:app --reload --port 8001

run-embedding:
	cd backend && PYTHONPATH=. ./venv/bin/uvicorn services.embedding.app.main:app --reload --port 8002

run-retrieval:
	cd backend && PYTHONPATH=. ./venv/bin/uvicorn services.retrieval.app.main:app --reload --port 8003

run-rag:
	cd backend && PYTHONPATH=. ./venv/bin/uvicorn services.rag.app.main:app --reload --port 8004

run-ml:
	cd backend && PYTHONPATH=. ./venv/bin/uvicorn services.ml.app.main:app --reload --port 8005

run-backends:
	$(MAKE) run-ingestion & $(MAKE) run-embedding & $(MAKE) run-retrieval & $(MAKE) run-rag & $(MAKE) run-ml & wait

run-mcp:
	PYTHONPATH=. ./backend/venv/bin/python -m mcp_service.main

test-mcp:
	./backend/venv/bin/pip install -q pytest-asyncio && PYTHONPATH=. ./backend/venv/bin/python -m pytest mcp_service/tests/ -v

test: test-backend test-gateway test-mcp

test-backend:
	cd backend && PYTHONPATH=. ./venv/bin/pytest tests/ -v

test-gateway:
	cd backend/services/gateway && npm test

lint: lint-backend lint-frontend

lint-backend:
	cd backend && ./venv/bin/ruff check .

lint-frontend:
	cd frontend && npm run lint

format: format-backend format-frontend

format-backend:
	cd backend && ./venv/bin/ruff format .

format-frontend:
	cd frontend && npm run lint:fix

stop-local:
	@echo "Stopping local API and frontend (ports 8000, 5173–5176)..."
	@pkill -f "uvicorn services\." 2>/dev/null || true
	@pkill -f "tsx watch src/index.ts" 2>/dev/null || true
	@pkill -f "vite" 2>/dev/null || true
	@echo "Done. You can run make start again."
