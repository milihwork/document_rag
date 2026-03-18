"""Prompt builder for RAG context injection."""


def build_prompt(question: str, context: str) -> str:
    """Build a prompt with context for the LLM."""
    return f"""
You are an AI assistant that answers questions strictly based on the provided context.

Answer only the question asked below. Do not repeat, list, or include other
questions and answers that appear in the context.

Context:
----------------
{context}
----------------

If the answer is not contained in the context, say:
"I don't know based on the provided documents."

Question:
{question}

Answer:
"""
