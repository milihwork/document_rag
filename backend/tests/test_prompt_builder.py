"""Tests for prompt builder."""

from shared.prompt_builder import build_prompt


def test_build_prompt_includes_question_and_context():
    """Prompt should contain question and context."""
    question = "What is RAG?"
    context = "RAG means Retrieval Augmented Generation."
    prompt = build_prompt(question, context)
    assert question in prompt
    assert context in prompt
    assert "Answer:" in prompt
