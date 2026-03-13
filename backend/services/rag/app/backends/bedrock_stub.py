"""Stub for AWS Bedrock LLM backend. Implement with boto3 and Bedrock API."""

from . import register
from .base import LLM


@register("bedrock")
class BedrockLLMBackend(LLM):
    """Placeholder for Bedrock chat/completion. Implement with boto3."""

    def complete(self, prompt: str, n_predict: int = 256, temperature: float = 0.2) -> str:
        raise NotImplementedError(
            "Bedrock LLM backend not implemented. "
            "Add boto3 and implement invoke_model for the chosen Bedrock model."
        )
