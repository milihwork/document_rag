# MCP Server (AI Agent Access) 🧩

The Document RAG system can be used as a **tool provider** for AI agents (Cursor, Claude Desktop, etc.) via the **Model Context Protocol (MCP)**. The MCP server exposes three tools that call the existing RAG services over HTTP. It acts as a thin orchestration layer: no changes to backend service logic, only a new client that agents can connect to.

---

## Prerequisites ✅

- **Python 3.11+**
- Backend services running (Embedding, Retrieval, RAG, Ingestion). See [local-development.md](local-development.md) or run `make up` for Docker.

---

## Install 📦

From the project root:

```bash
cd mcp_service
pip install -r requirements.txt
cd ..
```

Or use the backend venv and install MCP deps there:

```bash
./backend/venv/bin/pip install -r mcp_service/requirements.txt
```

---

## Configuration ⚙️

Set these environment variables if your services are not on localhost (defaults are for local dev):

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_SERVICE_URL` | `http://localhost:8002` | Embedding service base URL |
| `RETRIEVAL_SERVICE_URL` | `http://localhost:8003` | Retrieval service base URL |
| `RAG_SERVICE_URL` | `http://localhost:8004` | RAG orchestration service base URL |
| `INGESTION_SERVICE_URL` | `http://localhost:8001` | Ingestion service base URL |
| `TOP_K` | `3` | Number of chunks to return for search |

Optional: create `mcp_service/.env` or set env in your shell before running the server.

---

## Run the MCP server ▶️

From the **project root** (so that `mcp_service` is a resolvable package):

```bash
python -m mcp_service.main
```

Or use the Makefile target:

```bash
make run-mcp
```

The server runs over **stdio** by default. Keep it running and point your MCP client to the same command so the client can spawn and talk to it.

---

## Connect from Cursor 💻

1. Open Cursor settings (e.g. **Cursor Settings → MCP** or the MCP configuration file).
2. Add a new MCP server. Example configuration (adjust paths to your repo):

   **Command:** `python`  
   **Args:** `-m`, `mcp_service.main`  
   **Cwd:** path to your `document_rag` repo root

   So the server is started with `python -m mcp_service.main` with the working directory set to the project root.

3. Restart or reload Cursor so it discovers the tools.
4. In chat, you should be able to use: **search_documents**, **ask_rag**, **ingest_document**.

---

## Connect from Claude Desktop 🖥️

1. Edit your Claude Desktop MCP config (e.g. `~/Library/Application Support/Claude/claude_desktop_config.json` on macOS).
2. Add a server entry that runs the MCP server, for example:

   ```json
   {
     "mcpServers": {
       "document-rag": {
         "command": "python",
         "args": ["-m", "mcp_service.main"],
         "cwd": "/absolute/path/to/document_rag"
       }
     }
   }
   ```

3. Restart Claude Desktop. The tools will appear when the server is used.

---

## Tools 🧰

| Tool | Input | Description |
|------|--------|-------------|
| **search_documents** | `query: str` | Vector similarity search over the document knowledge base. Returns top matching text chunks and their sources. |
| **ask_rag** | `question: str` | Full RAG: retrieves relevant chunks, builds context, and generates an answer with the LLM. Returns the answer and source list. |
| **ingest_document** | `document: str`, `source: str` (optional, default `"mcp"`) | Adds document text to the knowledge base: chunks it, embeds via the Embedding service, and stores via the Ingestion service (`POST /ingest/text`). Returns status and chunk count. |

---

## Example use (from an agent) 🤖

- **Search:** “Find passages about authentication” → agent calls `search_documents(query="authentication")` and gets formatted chunks.
- **Ask:** “What does this doc say about security?” → agent calls `ask_rag(question="What does this doc say about security?")` and gets an answer with sources.
- **Ingest:** “Add this to the knowledge base: …” → agent calls `ingest_document(document="...", source="user-paste")` and gets a confirmation.

---

## Tests 🧪

From the project root, with a venv that has `mcp_service` dependencies installed:

```bash
PYTHONPATH=. pytest mcp_service/tests/ -v
```

Or use the Makefile:

```bash
make test-mcp
```

Tests mock HTTP calls to the backend services; no live services are required.
