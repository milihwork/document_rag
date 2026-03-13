"""Stub for AWS Bedrock embedding backend. Add boto3 and implement for production."""

from . import register
from .base import EmbeddingBackend


@register("bedrock")
class BedrockEmbeddingBackend(EmbeddingBackend):
    """Placeholder for Bedrock embeddings. Implement with boto3 and Bedrock API."""

    def embed(self, text: str) -> list[float]:
        raise NotImplementedError(
            "Bedrock embedding backend not implemented. "
            "Add boto3 and implement invoke_model for the chosen Bedrock embedding model."
        )

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        raise NotImplementedError(
            "Bedrock embedding backend not implemented. Add boto3 and implement batch embedding."
        )
