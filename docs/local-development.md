# Local development (Docker only for Qdrant)

Run the Gateway, Ingestion, Embedding, Retrieval, RAG, frontend, and LLM on your host; only Qdrant runs in Docker.

## Prerequisites

- Python 3.11+
- Node.js (for the frontend and the Gateway; LTS recommended)
- Docker (for Qdrant only)
- Optional: [llama.cpp](https://github.com/ggerganov/llama.cpp) and a GGUF model for the LLM (or set `LLM_URL` to another server)

## Steps (in order)

### 1. Start Qdrant

From the project root:

```bash
make qdrant
```

This starts the Qdrant container on port 6333 with persistent storage. Leave it running.

### 2. Backend Python environment

From the project root:

```bash
cd backend
python3.11 -m venv venv
source venv/bin/activate   # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Optional: copy and edit the repo-wide env file if you want to override defaults (for example if your LLM is not on `http://localhost:8080`):

```bash
cp .env.example .env
```

The Python backend services load the root `.env`, so this is the recommended place to set values such as `LLM_URL`, `ML_SERVICE_ENABLED`, `SAFEGUARD_ENABLED`, and retrieval settings. The file `backend/.env.example` is kept as a backend-focused reference, but the root `.env` is the primary config file for this repository.

Defaults already point to `http://localhost:8001`–`8004` for the four Python services plus the Gateway and `localhost:6333` for Qdrant, so no extra env is required for local inter-service URLs.

### 3. Gateway Node.js environment

From the project root:

```bash
cd backend/services/gateway
npm install
cd ../../..
```

### 4. Start the backend services

Run each command in its **own terminal**, from the **project root**:

**Terminal 1 — Embedding (8002):**
```bash
make run-embedding
```

**Terminal 2 — Retrieval (8003):**
```bash
make run-retrieval
```

**Terminal 3 — Ingestion (8001):**
```bash
make run-ingestion
```

**Terminal 4 — RAG (8004):**
```bash
make run-rag
```

**Terminal 5 — Gateway (8000, Express + TypeScript):**
```bash
make run-gateway
```

Recommended order: start **Embedding** and **Retrieval** first (they only depend on Qdrant or the embedding model). Then **Ingestion** and **RAG** (they call Embedding and Retrieval). Then **Gateway** (it calls Ingestion and RAG).

**Optional — one terminal:** From the project root, `make run-backends` starts the five Python services (ingestion, embedding, retrieval, rag, ml) in the same terminal (logs interleaved). Run the gateway separately with `make run-gateway` in another terminal if needed. Stop with Ctrl+C. Prefer separate terminals if you need clear per-service logs.

If you see "Upstream error while proxying chat request" in the UI, ensure the RAG service is running on port 8004 and that the Gateway can reach it (check `RAG_URL` if you run Gateway in Docker).

### 5. Start the LLM

In another terminal (from the project root):

Before first use, run `make init-llama` once and place a GGUF model in `models/`. See [../models/README.md](../models/README.md) for the default filename and setup notes.

```bash
make llm
```

Or run your own LLM server and set `LLM_URL` in the root `.env` (for example `LLM_URL=http://localhost:8080`). The RAG service uses this URL for completions.

### 6. Start the frontend

In another terminal:

```bash
make frontend
```

The Vite dev server runs at http://localhost:5173 and proxies `/api` to the Gateway at http://localhost:8000. Open the URL shown in the terminal. OpenAPI docs (interactive UI) are at http://localhost:8000/openapi/docs when the Gateway is running; the spec is at http://localhost:8000/openapi.json.

### 7. MCP server (optional)

To use the RAG system as an MCP tool provider for Cursor, Claude Desktop, or other MCP-compatible clients:

1. Ensure the backend services (and optionally the LLM) are running as above.
2. From the project root, run the MCP server:

   ```bash
   make run-mcp
   ```

   Or: `python -m mcp_service.main` (with a venv that has `mcp_service` dependencies installed; see `mcp_service/requirements.txt`).

3. Configure your MCP client to start the server with command `python`, args `-m`, `mcp_service.main`, and working directory set to the repo root.

See [mcp.md](mcp.md) for full setup, environment variables, and tool descriptions.

## Reference: components and ports

| Component | Command | Port |
|-----------|---------|------|
| Qdrant | `make qdrant` | 6333 |
| Embedding | `make run-embedding` | 8002 |
| Retrieval | `make run-retrieval` | 8003 |
| Ingestion | `make run-ingestion` | 8001 |
| RAG | `make run-rag` | 8004 |
| Gateway | `make run-gateway` | 8000 |
| Backends | `make run-backends` | 8001–8004 |
| LLM | `make llm` | 8080 (default) |
| Frontend | `make frontend` | 5173 |
| MCP Server | `make run-mcp` | stdio (no port) |

## Optional: environment variables

If you use the root `.env`, common variables include:

- `QDRANT_HOST`, `QDRANT_PORT` — for the Retrieval service (defaults: `localhost`, `6333`).
- `LLM_URL` — for the RAG service (default: `http://localhost:8080`).

Service URLs (e.g. `EMBEDDING_URL`, `RETRIEVAL_URL`) default to `http://localhost:8002`, `http://localhost:8003`, etc., so they do not need to be set when running everything on the host.

## Linting

From the project root you can run:

- **`make lint`** — runs the backend linter (Ruff) and the frontend linter (ESLint).
- **`make lint-backend`** — Ruff only (config in `backend/pyproject.toml`). Requires `pip install -r backend/requirements-dev.txt` so Ruff is available in the backend venv.
- **`make lint-frontend`** — ESLint only (config in `frontend/.eslintrc.cjs`).
- **`make format`** — format backend with Ruff and run ESLint with `--fix` in the frontend.

Backend uses [Ruff](https://docs.astral.sh/ruff/) for linting and formatting; frontend uses ESLint with TypeScript and React rules.
