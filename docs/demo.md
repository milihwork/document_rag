# Demo Guide 🎬

Use this short walkthrough when showing the project on GitHub.

## 60-second pitch ⏱️

Document RAG is a local-first RAG platform for grounded question answering over PDFs and text documents. It demonstrates an end-to-end AI workflow with ingestion, chunking, embeddings, vector search, reranking, query rewriting, source attribution, and optional LLM-based analysis, all behind a modular multi-service architecture.

## Suggested demo flow ▶️

1. Start the stack with `make up`, `make llm`, and `make frontend`.
2. Open `http://localhost:5173`.
3. Upload a small PDF or ingest text with the MCP tool.
4. Ask a question that requires retrieval from the uploaded document.
5. Point out that the answer includes sources and is grounded in retrieved chunks.

When everything is up and running locally, the system looks like this:

![All services running locally](up-and-running-all.png)

## Preferred local development (5 terminals) 💻

This is the preferred way to run the stack locally for development: one terminal per concern, with only Qdrant in Docker.

**Prerequisites:**

- Ensure Docker is running (`docker ps` to verify).
- **First-time only:** Create the backend Python venv and install dependencies so `make run-backends` can find `backend/venv/bin/uvicorn`. See [Local development](local-development.md) → “Backend Python environment”.

| Terminal | Command | Purpose |
|----------|---------|---------|
| 1 | `make qdrant` | Vector store (Docker) |
| 2 | `make frontend` | Vite dev server |
| 3 | `make llm` | LLM server (foreground) |
| 4 | `make run-backends` | Ingestion, embedding, retrieval, rag, ml |
| 5 | `make run-gateway` | Gateway (Node, port 8000) |

Then open `http://localhost:5173` and follow the demo flow (upload PDF, ask questions, show sources).

**Why this setup:** Running each piece in its own terminal gives you separate logs and the ability to restart one service without affecting the others. Keeping only Qdrant in Docker and running gateway and backends on the host allows hot-reload and easier debugging. Start Qdrant first so the other services can connect to the vector store.

## Example prompts 💡

Try questions that show retrieval instead of generic chat:

* "Summarize the main idea of this document."
* "What does the document say about architecture?"
* "List the key risks mentioned in the file."
* "Which sections talk about security or safeguards?"

## What to point out during the demo 📌

* The app is not a single monolith. Ingestion, embedding, retrieval, RAG, ML, and Gateway concerns are separated.
* Retrieval quality is improved with optional BGE reranking and query rewriting.
* The default stack is local-first, but the backend interfaces are configurable.
* The same backend can be used through the web UI or through MCP tools for agents.

