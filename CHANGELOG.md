# Changelog

All notable changes to this repository will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [2026-03-18]

### Added
- LangChain + LangSmith (RAG service only): optional, feature-flagged orchestration enhancements.
- LangChain adapters in `backend/services/rag/app/langchain_adapters.py`:
  - `BackendLLM`: wraps existing pluggable LLM backend (`_get_llm().complete(...)`).
  - `HttpVectorRetriever`: calls Embedding + Retrieval services over HTTP and returns LangChain `Document`s.
- Feature flags in `backend/services/rag/app/config/settings.py`:
  - `LANGCHAIN_ENABLED`, `MULTIQUERY_ENABLED`, `MULTIQUERY_N`, `LANGCHAIN_RETRIEVER_TOP_K`, `LANGSMITH_TRACING`.
- Optional LangChain retrieval path in `backend/services/rag/app/main.py`:
  - multi-query retrieval (via LangChain `MultiQueryRetriever`) + doc dedupe + reuse existing reranker when enabled.
  - LangSmith trace hooks (`rag.ask`, `rag.langchain_retrieve`) when tracing is enabled.
- New smoke test `backend/tests/test_rag_langchain_smoke.py` covering the LangChain multi-query retrieval path with monkeypatched embed/search/LLM.

### Changed
- `backend/services/rag/requirements.txt`: add `langchain`, `langchain-core`, `langsmith`.
- `.env.example`: add LangChain/LangSmith feature flags (`LANGCHAIN_ENABLED`, `MULTIQUERY_*`, `LANGCHAIN_RETRIEVER_TOP_K`, `LANGSMITH_TRACING`) and LangSmith env var hints.
- Embedding service (local / sentence-transformers backend): enable embedding normalization by default and add runtime config knobs (`EMBEDDING_NORMALIZE`, optional `EMBEDDING_DEVICE`, `EMBEDDING_BATCH_SIZE`, `EMBEDDING_MAX_LENGTH`). Changing `EMBEDDING_MODEL` or `EMBEDDING_NORMALIZE` requires re-embedding stored vectors and ensuring Retrieval `VECTOR_SIZE` matches the embedding dimension.
- Embedding backend naming: add **Hugging Face** as the default embedding backend; `EMBEDDING_BACKEND=huggingface` is an explicit alias of the sentence-transformers backend (previous `local` remains supported). Update `docker-compose.yml` and env examples to use `huggingface` for clarity.
- Gateway: add dev-only `GET /debug/config` endpoint (allowlisted runtime config snapshot; disabled in production).
- Frontend (dev-only): add **Environment details** button + modal (loads `GET /debug/config`, shows JSON, copy-to-clipboard).
- `docs/local-development.md`: document the dev-only Environment details popup and optional LangChain path.

## [2026-03-16]

### Changed
- Clarified `.env.example` defaults and `LLM_URL` usage for local vs Docker environments.
- Added root endpoint redirects to API docs across services.
- Increased API request timeout (90s → 180s).
- Fixed Docker Compose configuration issues.
- CI workflow: ignore docs/markdown-only changes for some events.

### Fixed
- Gateway tests.
- MCP tests.

### Docs
- README and `docs/ARTICLE.md` updates (links, cover image, publication link, refactors).

## [2026-03-14]

### Docs
- `docs/ARTICLE.md` updates (image paths, architecture section adjustments).
- README + article improvements.

## [2026-03-13]

### Added
- Initial end-to-end local-first RAG stack (multi-service architecture).
- Lazy-loading for LLM backends and vector store backends.

### Fixed
- Gateway test fixes.
- Backend lint fix.

