"""RAG service: POST /ask — embed query, search, build prompt, call LLM, return answer + sources."""

import logging
import os
import time

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.responses import RedirectResponse
from pydantic import BaseModel

from services.safeguard import get_safeguard
from shared.contracts import (
    KEY_ANSWER,
    KEY_CHUNKS,
    KEY_EMBEDDING,
    KEY_INJECTION,
    KEY_INTENT,
    KEY_IS_INJECTION,
    KEY_OK,
    KEY_QUERY,
    KEY_QUERY_VECTOR,
    KEY_QUESTION,
    KEY_REASON,
    KEY_SCORE,
    KEY_SOURCE,
    KEY_SOURCES,
    KEY_STATUS,
    KEY_SUFFICIENT,
    KEY_TEXT,
    KEY_TOP_K,
    PATH_ANALYZE,
    PATH_ASK,
    PATH_EMBED,
    PATH_HEALTH,
    PATH_SCORE_RETRIEVAL,
    PATH_SEARCH,
)
from shared.prompt_builder import build_prompt
from shared.reranker import get_reranker

from .backends import get_backend
from .config.settings import settings

if settings.LANGSMITH_TRACING:
    # LangChain tracing is primarily controlled via LANGCHAIN_TRACING_V2=true.
    # We allow this repo-level toggle to enable tracing without forcing a specific provider.
    os.environ.setdefault("LANGCHAIN_TRACING_V2", "true")

try:
    from langsmith import traceable  # type: ignore
except Exception:  # pragma: no cover
    def traceable(*_args, **_kwargs):  # type: ignore
        def _decorator(fn):
            return fn

        return _decorator

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# If LANGCHAIN_ENABLED, validate imports at startup so we fail fast with a clear error.
_langchain_import_error: str | None = None
if settings.LANGCHAIN_ENABLED:
    try:
        from langchain_core.prompts import PromptTemplate  # noqa: F401
        from .langchain_adapters import (  # noqa: F401
            HttpVectorRetriever,
            RetrievalMapping,
            dedupe_documents,
        )
    except (ImportError, ModuleNotFoundError) as e:
        _langchain_import_error = str(e)
        logger.error(
            "LangChain is enabled but imports failed: %s. "
            "Install RAG dependencies (e.g. pip install -r backend/requirements.txt) "
            "or set LANGCHAIN_ENABLED=false.",
            _langchain_import_error,
            exc_info=True,
        )

app = FastAPI(
    title="RAG Orchestration Service",
    description="Question -> answer + sources via Embedding, Retrieval, LLM",
)

_llm_backend = None
_safeguard = None
_query_rewriter = None


def _get_llm():
    global _llm_backend
    if _llm_backend is None:
        _llm_backend = get_backend()
    return _llm_backend


def _get_safeguard():
    global _safeguard
    if _safeguard is None:
        _safeguard = get_safeguard()
    return _safeguard


def _get_query_rewriter():
    global _query_rewriter
    if _query_rewriter is None:
        from shared.query_rewriter import get_query_rewriter
        _query_rewriter = get_query_rewriter(
            _get_llm(), max_words=settings.QUERY_REWRITER_MAX_WORDS
        )
    return _query_rewriter


async def _embed(text: str) -> list[float]:
    """Call Embedding service for single text."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.EMBEDDING_URL}{PATH_EMBED}",
            json={KEY_TEXT: text},
        )
        r.raise_for_status()
        return (r.json())[KEY_EMBEDDING]


async def _search(query_vector: list[float], top_k: int | None = None) -> list[dict]:
    """Call Retrieval service. Returns list of {text, source}."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.RETRIEVAL_URL}{PATH_SEARCH}",
            json={
                KEY_QUERY_VECTOR: query_vector,
                KEY_TOP_K: top_k or settings.TOP_K,
            },
        )
        r.raise_for_status()
        return (r.json())[KEY_CHUNKS]


@traceable(name="rag.langchain_retrieve")
async def _langchain_retrieve(question: str, retrieval_query: str) -> list[dict]:
    """Retrieve chunks using LangChain multi-query (feature flagged)."""

    if _langchain_import_error:
        raise NotImplementedError(
            f"LangChain is not available: {_langchain_import_error}. "
            "Install RAG service dependencies or disable LANGCHAIN_ENABLED."
        )

    try:
        from .langchain_adapters import (
            HttpVectorRetriever,
            RetrievalMapping,
            dedupe_documents,
        )
    except (ImportError, ModuleNotFoundError) as e:  # pragma: no cover
        raise NotImplementedError(
            f"LangChain is not available: {e!s}. "
            "Install RAG service dependencies or disable LANGCHAIN_ENABLED."
        ) from e

    reranker_enabled = settings.RERANKER_PROVIDER not in ("", "none")
    candidate_top_k = (
        settings.LANGCHAIN_RETRIEVER_TOP_K
        if reranker_enabled
        else settings.RERANK_TOP_K
    )

    retriever = HttpVectorRetriever(
        embed=_embed,
        search=_search,
        top_k=candidate_top_k,
        mapping=RetrievalMapping(text_key=KEY_TEXT, source_key=KEY_SOURCE, score_key=KEY_SCORE),
    )

    try:
        from langchain_core.prompts import PromptTemplate
    except (ImportError, ModuleNotFoundError) as e:  # pragma: no cover
        raise NotImplementedError(
            f"LangChain is not available: {e!s}. "
            "Install RAG service dependencies or disable LANGCHAIN_ENABLED."
        ) from e

    docs = []
    if settings.MULTIQUERY_ENABLED:
        n = max(1, int(settings.MULTIQUERY_N))
        prompt_tpl = (
            "You are a search query generator.\n"
            f"Given the user question, write {n} different search queries that could "
            "retrieve relevant passages.\n"
            "Return one query per line, no numbering, no extra text.\n\n"
            "Question: {question}\n"
        )
        prompt = PromptTemplate(
            input_variables=["question"],
            template=prompt_tpl,
        )
        gen_prompt = prompt.format(question=retrieval_query)
        llm = _get_llm()
        raw = llm.complete(gen_prompt)
        queries = [s.strip() for s in raw.strip().splitlines() if s.strip()]
        if retrieval_query.strip() not in queries:
            queries.insert(0, retrieval_query)
        all_docs = []
        for q in queries[: n + 1]:
            # LangChain 1.x retrievers use Runnable interface (ainvoke).
            part = await retriever.ainvoke(q)
            all_docs.extend(part)
        docs = dedupe_documents(all_docs)
    else:
        docs = await retriever.ainvoke(retrieval_query)

    docs = dedupe_documents(docs)

    # Convert docs back to the service's chunk format.
    chunks = [
        {
            KEY_TEXT: d.page_content,
            KEY_SOURCE: d.metadata.get(KEY_SOURCE, d.metadata.get("source", "unknown")),
        }
        for d in docs
        if d.page_content
    ]

    if not reranker_enabled or not chunks:
        return chunks[: settings.RERANK_TOP_K]

    doc_texts = [c[KEY_TEXT] for c in chunks]
    top_texts = get_reranker().rerank(
        question,
        doc_texts,
        top_k=settings.RERANK_TOP_K,
    )
    text_to_chunk = {}
    for c in chunks:
        t = c[KEY_TEXT]
        if t not in text_to_chunk:
            text_to_chunk[t] = c
    return [text_to_chunk[t] for t in top_texts if t in text_to_chunk]


async def _analyze_query(query: str) -> dict:
    """Call ML service for injection detection and query classification."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.ML_SERVICE_URL}{PATH_ANALYZE}",
            json={KEY_QUERY: query},
        )
        r.raise_for_status()
        return r.json()


async def _score_retrieval(query: str, chunks: list[dict]) -> dict:
    """Call ML service to score retrieval quality."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        r = await client.post(
            f"{settings.ML_SERVICE_URL}{PATH_SCORE_RETRIEVAL}",
            json={
                KEY_QUERY: query,
                KEY_CHUNKS: [
                    {
                        KEY_TEXT: c[KEY_TEXT],
                        KEY_SOURCE: c.get(KEY_SOURCE, "unknown"),
                    }
                    for c in chunks
                ],
            },
        )
        r.raise_for_status()
        return r.json()


class AskRequest(BaseModel):
    question: str


@app.get("/")
def root():
    """Redirect root to API docs."""
    return RedirectResponse(url="/docs", status_code=302)


@app.post(PATH_ASK)
@traceable(name="rag.ask")
async def ask(request: AskRequest):
    """Run RAG: embed question -> search -> prompt -> LLM -> {question, answer, sources}."""
    start = time.perf_counter()
    logger.info("RAG /ask for question: %s", request.question[:80])

    try:
        if settings.SAFEGUARD_ENABLED:
            if not _get_safeguard().validate_input(request.question):
                logger.warning(
                    "Query blocked by safeguard: %s",
                    request.question[:80],
                )
                raise HTTPException(
                    status_code=403,
                    detail="Query blocked by safeguard policy",
                )

        # ML Service: injection detection and query classification
        if settings.ML_SERVICE_ENABLED:
            try:
                ml_result = await _analyze_query(request.question)
                injection = ml_result.get(KEY_INJECTION, {})
                if injection.get(KEY_IS_INJECTION, False):
                    confidence = injection.get("confidence", 0.0)
                    if confidence >= settings.INJECTION_THRESHOLD:
                        logger.warning(
                            "Query blocked by injection detector (confidence=%.2f): %s",
                            confidence,
                            request.question[:80],
                        )
                        raise HTTPException(
                            status_code=403,
                            detail="Potential prompt injection detected",
                        )
                intent = ml_result.get(KEY_INTENT, {})
                logger.info(
                    "Query intent: %s (confidence=%.2f)",
                    intent.get(KEY_INTENT, "unknown"),
                    intent.get("confidence", 0.0),
                )
            except httpx.HTTPError as e:
                logger.warning("ML service unavailable, continuing without: %s", e)

        # Query rewriting for better retrieval
        retrieval_query = request.question
        if settings.QUERY_REWRITING_ENABLED:
            try:
                retrieval_query = _get_query_rewriter().rewrite(request.question)
                if retrieval_query != request.question:
                    logger.info(
                        "Query rewritten: original=%r, rewritten=%r",
                        request.question[:80],
                        retrieval_query[:80],
                    )
            except Exception as e:
                logger.warning("Query rewriting failed, using original: %s", e)
                retrieval_query = request.question

        if settings.LANGCHAIN_ENABLED:
            chunks = await _langchain_retrieve(request.question, retrieval_query)
        else:
            query_embedding = await _embed(retrieval_query)

            reranker_enabled = settings.RERANKER_PROVIDER not in ("", "none")
            if reranker_enabled:
                chunks = await _search(
                    query_embedding, top_k=settings.VECTOR_SEARCH_TOP_K
                )
                doc_texts = [c[KEY_TEXT] for c in chunks]
                top_texts = get_reranker().rerank(
                    request.question,
                    doc_texts,
                    top_k=settings.RERANK_TOP_K,
                )
                # Map reranked texts back to chunks (preserve order and source)
                text_to_chunk = {}
                for c in chunks:
                    t = c[KEY_TEXT]
                    if t not in text_to_chunk:
                        text_to_chunk[t] = c
                chunks = [text_to_chunk[t] for t in top_texts if t in text_to_chunk]
            else:
                chunks = await _search(
                    query_embedding, top_k=settings.RERANK_TOP_K
                )

        # ML Service: score retrieval quality after reranking
        if settings.ML_SERVICE_ENABLED and chunks:
            try:
                retrieval_result = await _score_retrieval(request.question, chunks)
                score = retrieval_result.get(KEY_SCORE, 0.5)
                sufficient = retrieval_result.get(KEY_SUFFICIENT, True)
                reason = retrieval_result.get(KEY_REASON, "")
                logger.info(
                    "Retrieval score: %.2f, sufficient=%s, reason=%s",
                    score,
                    sufficient,
                    reason[:50],
                )
                if not sufficient and score < settings.RETRIEVAL_SCORE_THRESHOLD:
                    logger.warning(
                        "Low retrieval quality (score=%.2f): %s",
                        score,
                        reason,
                    )
            except httpx.HTTPError as e:
                logger.warning("ML service scoring unavailable: %s", e)

        context = "\n".join(c[KEY_TEXT] for c in chunks)
        sources = list({c[KEY_SOURCE] for c in chunks})

        prompt = build_prompt(request.question, context)
        answer = _get_llm().complete(prompt)

        if settings.SAFEGUARD_ENABLED:
            if not _get_safeguard().validate_output(answer):
                logger.warning(
                    "Response blocked by safeguard: %s",
                    answer[:80],
                )
                raise HTTPException(
                    status_code=403,
                    detail="Response blocked by safeguard policy",
                )

        elapsed = (time.perf_counter() - start) * 1000
        logger.info("RAG completed in %.0fms, sources: %s", elapsed, sources)

        return {
            KEY_QUESTION: request.question,
            KEY_ANSWER: answer,
            KEY_SOURCES: sources,
        }
    except httpx.HTTPError as e:
        logger.exception("RAG failed: %s", e)
        raise HTTPException(status_code=502, detail=f"Upstream error: {e}")
    except NotImplementedError as e:
        raise HTTPException(status_code=501, detail=str(e))


@app.get(PATH_HEALTH)
def health():
    return {KEY_STATUS: KEY_OK}


@app.get("/config")
def config():
    """Return a non-secret, allowlisted runtime config snapshot."""

    return {
        # Core wiring (non-secret)
        "EMBEDDING_URL": settings.EMBEDDING_URL,
        "RETRIEVAL_URL": settings.RETRIEVAL_URL,
        "LLM_BACKEND": settings.LLM_BACKEND,
        "LLM_URL": settings.LLM_URL,
        # Retrieval quality knobs
        "TOP_K": settings.TOP_K,
        "RERANKER_PROVIDER": settings.RERANKER_PROVIDER,
        "VECTOR_SEARCH_TOP_K": settings.VECTOR_SEARCH_TOP_K,
        "RERANK_TOP_K": settings.RERANK_TOP_K,
        # Safeguards + ML
        "SAFEGUARD_ENABLED": settings.SAFEGUARD_ENABLED,
        "SAFEGUARD_PROVIDER": settings.SAFEGUARD_PROVIDER,
        "ML_SERVICE_ENABLED": settings.ML_SERVICE_ENABLED,
        "ML_SERVICE_URL": settings.ML_SERVICE_URL,
        "INJECTION_THRESHOLD": settings.INJECTION_THRESHOLD,
        "RETRIEVAL_SCORE_THRESHOLD": settings.RETRIEVAL_SCORE_THRESHOLD,
        # Query rewriting
        "QUERY_REWRITING_ENABLED": settings.QUERY_REWRITING_ENABLED,
        "QUERY_REWRITER_PROVIDER": settings.QUERY_REWRITER_PROVIDER,
        "QUERY_REWRITER_MAX_WORDS": settings.QUERY_REWRITER_MAX_WORDS,
        # LangChain/LangSmith (non-secret flags only)
        "LANGCHAIN_ENABLED": settings.LANGCHAIN_ENABLED,
        "MULTIQUERY_ENABLED": settings.MULTIQUERY_ENABLED,
        "MULTIQUERY_N": settings.MULTIQUERY_N,
        "LANGCHAIN_RETRIEVER_TOP_K": settings.LANGCHAIN_RETRIEVER_TOP_K,
        "LANGSMITH_TRACING": settings.LANGSMITH_TRACING,
    }
