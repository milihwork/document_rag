"""Text chunking with sentence-boundary awareness."""

import re


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Split text into chunks of approximately max_chars, respecting sentence boundaries.
    """
    sentences = re.split(r"(?<=[.!?]) +", text)

    chunks = []
    current_chunk = ""

    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += " " + sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
