"""ML Service: POST /analyze — injection detection, query classification, retrieval scoring."""

import logging
import time

from fastapi import FastAPI
from pydantic import BaseModel

from shared.contracts import KEY_OK, KEY_STATUS, PATH_HEALTH

from .components.factory import (
    get_document_classifier,
    get_injection_detector,
    get_query_classifier,
    get_retrieval_scorer,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="ML Service",
    description="Injection detection, query classification, and retrieval scoring",
)

PATH_ANALYZE = "/analyze"
PATH_SCORE_RETRIEVAL = "/score"
PATH_CLASSIFY = "/classify"


class ChunkInput(BaseModel):
    text: str
    source: str = "unknown"


class AnalyzeRequest(BaseModel):
    query: str
    chunks: list[ChunkInput] | None = None


class InjectionResponse(BaseModel):
    is_injection: bool
    confidence: float
    reason: str


class IntentResponse(BaseModel):
    intent: str
    confidence: float


class RetrievalScoreResponse(BaseModel):
    score: float
    sufficient: bool
    reason: str


class AnalyzeResponse(BaseModel):
    injection: InjectionResponse
    intent: IntentResponse
    retrieval_score: RetrievalScoreResponse | None = None


class ScoreRequest(BaseModel):
    query: str
    chunks: list[ChunkInput]


class ClassifyRequest(BaseModel):
    text_sample: str


class ClassifyResponse(BaseModel):
    category: str
    confidence: float


@app.post(PATH_ANALYZE)
async def analyze(request: AnalyzeRequest) -> AnalyzeResponse:
    """
    Analyze a query for injection attempts, classify intent, and optionally score retrieval.

    - injection: Detects prompt injection attempts
    - intent: Classifies query as question/command/search/clarification/other
    - retrieval_score: If chunks provided, scores retrieval quality
    """
    start = time.perf_counter()
    logger.info("ML /analyze for query: %s", request.query[:80])

    injection_result = get_injection_detector().detect(request.query)
    intent_result = get_query_classifier().classify(request.query)

    retrieval_score = None
    if request.chunks:
        chunks_dict = [{"text": c.text, "source": c.source} for c in request.chunks]
        score_result = get_retrieval_scorer().score(request.query, chunks_dict)
        retrieval_score = RetrievalScoreResponse(
            score=score_result.score,
            sufficient=score_result.sufficient,
            reason=score_result.reason,
        )

    elapsed = (time.perf_counter() - start) * 1000
    logger.info("ML /analyze completed in %.0fms", elapsed)

    return AnalyzeResponse(
        injection=InjectionResponse(
            is_injection=injection_result.is_injection,
            confidence=injection_result.confidence,
            reason=injection_result.reason,
        ),
        intent=IntentResponse(
            intent=intent_result.intent,
            confidence=intent_result.confidence,
        ),
        retrieval_score=retrieval_score,
    )


@app.post(PATH_SCORE_RETRIEVAL)
async def score_retrieval(request: ScoreRequest) -> RetrievalScoreResponse:
    """Score retrieval quality for a query and chunks (called post-rerank)."""
    start = time.perf_counter()
    logger.info("ML /score for query: %s", request.query[:80])

    chunks_dict = [{"text": c.text, "source": c.source} for c in request.chunks]
    result = get_retrieval_scorer().score(request.query, chunks_dict)

    elapsed = (time.perf_counter() - start) * 1000
    logger.info("ML /score completed in %.0fms", elapsed)

    return RetrievalScoreResponse(
        score=result.score,
        sufficient=result.sufficient,
        reason=result.reason,
    )


@app.post(PATH_CLASSIFY)
async def classify_document(request: ClassifyRequest) -> ClassifyResponse:
    """Classify a document based on a text sample."""
    start = time.perf_counter()
    logger.info("ML /classify for text sample: %d chars", len(request.text_sample))

    result = get_document_classifier().classify(request.text_sample)

    elapsed = (time.perf_counter() - start) * 1000
    logger.info("ML /classify completed in %.0fms: category=%s", elapsed, result.category)

    return ClassifyResponse(
        category=result.category,
        confidence=result.confidence,
    )


@app.get(PATH_HEALTH)
def health():
    """Health check endpoint."""
    return {KEY_STATUS: KEY_OK}
