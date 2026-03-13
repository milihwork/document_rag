"""BGE reranker backend using cross-encoder."""

import logging

from sentence_transformers import CrossEncoder

from .base import BaseReranker

logger = logging.getLogger(__name__)


class BGEReranker(BaseReranker):
    """Rerank documents using BAAI/bge-reranker-base cross-encoder."""

    def __init__(self):
        logger.info("Loading BGE reranker model: BAAI/bge-reranker-base")
        self.model = CrossEncoder("BAAI/bge-reranker-base")

    def rerank(self, query: str, documents: list[str], top_k: int = 3) -> list[str]:
        if not documents:
            return []

        logger.info(
            "Reranking %d documents, returning top %d",
            len(documents),
            top_k,
        )
        pairs = [[query, doc] for doc in documents]
        scores = self.model.predict(pairs)

        ranked_docs = sorted(
            zip(documents, scores, strict=True),
            key=lambda x: x[1],
            reverse=True,
        )
        return [doc for doc, _ in ranked_docs[:top_k]]
