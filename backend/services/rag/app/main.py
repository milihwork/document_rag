"""RAG service: POST /ask — embed query, search, build prompt, call LLM, return answer + sources."""

import logging
import time

import httpx
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from shared.contracts import (
    KEY_ANSWER,
    KEY_CHUNKS,
    KEY_EMBEDDING,
    KEY_INJECTION,
    KEY_INTENT,
    KEY_IS_INJECTION,
    KEY_OK,
    KEY_QUERY,
    KEY_QUESTION,
    KEY_QUERY_VECTOR,
    KEY_REASON,
    KEY_RETRIEVAL_SCORE,
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

from .backends import get_backend
from .config.settings import settings
from shared.reranker import get_reranker
from services.safeguard import get_safeguard

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

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
                KEY_CHUNKS: [{KEY_TEXT: c[KEY_TEXT], KEY_SOURCE: c.get(KEY_SOURCE, "unknown")} for c in chunks],
            },
        )
        r.raise_for_status()
        return r.json()


class AskRequest(BaseModel):
    question: str


@app.post(PATH_ASK)
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
