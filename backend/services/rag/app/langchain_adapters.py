"""LangChain adapters for the existing RAG service architecture.

These adapters keep the current service boundaries intact:
- LLM calls still go through the configured backend (llama.cpp/OpenAI/etc.)
- Embedding + retrieval still go through the Embedding and Retrieval services (HTTP)
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable
from dataclasses import dataclass
from typing import Any

from langchain_core.documents import Document
from langchain_core.language_models.llms import LLM as LangChainLLM
from langchain_core.retrievers import BaseRetriever
from pydantic import ConfigDict


class BackendLLM(LangChainLLM):
    """Expose the repo's pluggable LLM backend as a LangChain LLM."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    backend: Any

    def __init__(self, backend: Any):
        super().__init__(backend=backend)

    @property
    def _llm_type(self) -> str:  # required by LangChain
        return "document_rag_backend"

    def _call(
        self,
        prompt: str,
        stop: list[str] | None = None,
        run_manager: Any | None = None,
        **kwargs: Any,
    ) -> str:
        # Our backend interface supports n_predict/temperature.
        text = self.backend.complete(
            prompt,
            n_predict=kwargs.get("n_predict"),
            temperature=kwargs.get("temperature"),
        )
        if stop:
            for s in stop:
                if s and s in text:
                    text = text.split(s)[0]
        return text


EmbedFn = Callable[[str], Awaitable[list[float]]]
SearchFn = Callable[[list[float], int | None], Awaitable[list[dict]]]


@dataclass(frozen=True)
class RetrievalMapping:
    """Map retrieval chunk dicts to LangChain Documents."""

    text_key: str = "text"
    source_key: str = "source"
    score_key: str = "score"


class HttpVectorRetriever(BaseRetriever):
    """Retriever that uses existing Embedding + Retrieval services over HTTP."""

    model_config = ConfigDict(arbitrary_types_allowed=True)
    embed: EmbedFn
    search: SearchFn
    top_k: int
    mapping: RetrievalMapping

    def __init__(
        self,
        *,
        embed: EmbedFn,
        search: SearchFn,
        top_k: int,
        mapping: RetrievalMapping | None = None,
    ):
        super().__init__(
            embed=embed,
            search=search,
            top_k=top_k,
            mapping=mapping or RetrievalMapping(),
        )

    def _get_relevant_documents(  # pragma: no cover
        self, query: str, *, run_manager: Any | None = None
    ) -> list[Document]:
        raise NotImplementedError(
            "Use `aget_relevant_documents` (async) in this service."
        )

    async def _aget_relevant_documents(
        self, query: str, *, run_manager: Any | None = None
    ) -> list[Document]:
        vec = await self.embed(query)
        chunks = await self.search(vec, self.top_k)
        docs: list[Document] = []
        for c in chunks:
            text = c.get(self.mapping.text_key, "") or ""
            if not text:
                continue
            metadata = {}
            source = c.get(self.mapping.source_key)
            if source:
                metadata["source"] = source
            score = c.get(self.mapping.score_key)
            if score is not None:
                metadata["score"] = score
            docs.append(Document(page_content=text, metadata=metadata))
        return docs


def dedupe_documents(docs: Iterable[Document]) -> list[Document]:
    """Deduplicate by (content, source). Preserves first-seen order."""

    seen: set[tuple[str, str]] = set()
    out: list[Document] = []
    for d in docs:
        src = str(d.metadata.get("source", ""))
        key = (d.page_content, src)
        if key in seen:
            continue
        seen.add(key)
        out.append(d)
    return out

