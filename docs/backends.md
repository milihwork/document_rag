# Adding New Backends (Modular Architecture)

The repo uses **config-driven backends** for embeddings, vector store, and LLM. You can add AWS Bedrock, pgvector, OpenAI, etc. by implementing one backend module and setting the right env var. No changes are needed in the Gateway, Ingestion, or frontend.

## Overview

| Area | Config key | Service | Initial backend | Add by implementing |
|------|------------|---------|------------------|----------------------|
| Embedding | `EMBEDDING_BACKEND` | `backend/services/embedding/` | `local` | New file in `app/backends/`, register, add env |
| Vector store | `VECTOR_BACKEND` | `backend/services/retrieval/` | `qdrant` | New file in `app/backends/`, register, add env |
| LLM | `LLM_BACKEND` | `backend/services/rag/` | `llama` | New file in `app/backends/`, register, add env |
| Reranker | `RERANKER_PROVIDER` | RAG uses `backend/services/reranker/` | `bge` | New file in `services/reranker/`, register in factory; `none` to disable |

---

## 1. New Embedding Backend (e.g. Bedrock)

**Contract:** Same as existing backends:

- `embed(text: str) -> list[float]`
- `embed_batch(texts: list[str]) -> list[list[float]]`

**Steps:**

1. In `backend/services/embedding/app/backends/`, add e.g. `bedrock.py` (or re-use the stub `bedrock_stub.py` and implement it).
2. Implement a class with `embed` and `embed_batch` methods. Use `@register("bedrock")` so it is selected when `EMBEDDING_BACKEND=bedrock`.
3. In `app/backends/__init__.py`, import the new module so it registers (e.g. `from app.backends import bedrock_impl`).
4. Document backend-specific env (e.g. `AWS_REGION`, `BEDROCK_EMBEDDING_MODEL_ID`, or credentials). Read them in your backend or in `app/config/settings.py`.
5. Add optional dependencies (e.g. `boto3`) to `backend/services/embedding/requirements.txt` if needed.

**Example (stub already present):** Replace the `NotImplementedError` in `bedrock_stub.py` with a real implementation calling Bedrock’s embedding API; no changes in Ingestion or RAG.

---

## 2. Vector Backend: pgvector (implemented)

**Contract:** Same as existing backends:

- `ensure_collection() -> None` — create table/collection if it does not exist
- `search(query_vector: list[float], top_k: int | None) -> list[dict]` — each dict has `text` and `source`
- `upsert(points: list[dict]) -> None` — each point has `id`, `vector`, and `payload` (with `text`, `source`)

**To use pgvector:**

1. Set `VECTOR_BACKEND=pgvector`.
2. Set `DATABASE_URL` to your PostgreSQL connection string (e.g. `postgresql://user:pass@localhost/document_rag`). Ensure the `pgvector` extension is available (e.g. run `CREATE EXTENSION IF NOT EXISTS vector` once).
3. Optional: `PGVECTOR_TABLE_NAME` (default `documents`), `VECTOR_SIZE` (default `384`), `TOP_K`.

Implementation: `backend/services/retrieval/app/backends/pgvector.py`. Ingestion and RAG keep calling the same Retrieval HTTP API.

---

## 3. LLM Backend: OpenAI (implemented) and others

**Contract:** Same as existing backends:

- `complete(prompt: str, n_predict: int = 256, temperature: float = 0.2) -> str` — returns generated text.

**To use OpenAI:**

1. Set `LLM_BACKEND=openai`.
2. Set `OPENAI_API_KEY` to your API key.
3. Optional: `OPENAI_MODEL` (default `gpt-4o-mini`), `OPENAI_BASE_URL` (for compatible endpoints).

Implementation: `backend/services/rag/app/backends/openai_backend.py`. The Gateway and other services are unchanged.

**To add another LLM backend (e.g. Bedrock):**

1. In `backend/services/rag/app/backends/`, add e.g. `bedrock_llm.py`. Implement a class with a `complete` method and register it (e.g. `@register("bedrock")`).
2. In `app/backends/__init__.py`, import the new module.
3. Add backend-specific env. Use `LLM_BACKEND=bedrock` to select it.
4. Add optional dependencies to `backend/services/rag/requirements.txt`.

---

## 4. Reranker backend: BGE (implemented) and adding new rerankers

**Contract:** Same as existing reranker backends:

- `rerank(query: str, documents: list[str], top_k: int = 3) -> list[str]` — returns top_k documents in relevance order.

**To use the BGE reranker (default):**

1. Set `RERANKER_PROVIDER=bge` (or leave default). RAG will fetch `VECTOR_SEARCH_TOP_K` candidates (default 20), rerank them, and pass `RERANK_TOP_K` (default 3) to the LLM.
2. To disable reranking: set `RERANKER_PROVIDER=none` or leave empty.

**To add another reranker backend:**

1. In `backend/services/reranker/`, add e.g. `my_reranker.py`. Implement a class with a `rerank(query, documents, top_k)` method (see `base.py` and `bge_reranker.py`).
2. In `factory.py`, import the new module and add a branch for the new provider name (e.g. `if provider == "my_reranker": return MyReranker()`).
3. Document backend-specific env. Use `RERANKER_PROVIDER=my_reranker` to select it.

Implementation: `backend/services/reranker/` (base, bge_reranker, factory). RAG imports `get_reranker()` when reranker is enabled.

---

## Env Summary

- **Embedding:** `EMBEDDING_BACKEND=local|bedrock|openai`; backend-specific vars per implementation.
- **Retrieval:** `VECTOR_BACKEND=qdrant|pgvector`; backend-specific vars (e.g. `QDRANT_*` for qdrant; `DATABASE_URL`, `PGVECTOR_TABLE_NAME` for pgvector).
- **RAG:** `LLM_BACKEND=llama|bedrock|openai`; **Reranker:** `RERANKER_PROVIDER=bge|none` (default `bge`); `VECTOR_SEARCH_TOP_K` (default 20), `RERANK_TOP_K` (default 3). LLM backend-specific vars (e.g. `LLM_URL` for llama, `OPENAI_API_KEY`/`OPENAI_MODEL` for openai, AWS vars for bedrock).

**Switching backends:** Set the corresponding `*_BACKEND` env var and the required backend-specific vars. No code or API contract changes; same HTTP endpoints and payloads.

See each service’s `app/config/settings.py` and the architecture docs for the exact contract and layout.
