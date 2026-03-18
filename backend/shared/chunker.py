"""Text chunking with sentence-boundary and Q&A awareness."""

import re

# Pattern to detect "Question:" (or "Question :") so we can split Q&A documents per pair
_QA_SPLIT_PATTERN = re.compile(r"\s*(?=Question\s*:)", re.IGNORECASE)


def _chunk_by_sentence(text: str, max_chars: int) -> list[str]:
    """Split text into chunks of ~max_chars, respecting sentence boundaries."""
    sentences = re.split(r"(?<=[.!?]) +", text)
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) < max_chars:
            current_chunk += " " + sentence if current_chunk else sentence
        else:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
            current_chunk = sentence
    if current_chunk.strip():
        chunks.append(current_chunk.strip())
    return chunks


def chunk_text(text: str, max_chars: int = 800) -> list[str]:
    """
    Split text into chunks of approximately max_chars.

    - If the text contains "Question:" (e.g. Q&A-style docs), splits so each chunk
      is one Q&A pair when possible, avoiding mixing multiple pairs in one chunk.
    - Otherwise splits by sentence boundaries.
    """
    if not text or not text.strip():
        return []

    # Q&A-aware: split by "Question:" so each chunk is one Q&A block when possible
    if re.search(r"Question\s*:", text, re.IGNORECASE):
        segments = _QA_SPLIT_PATTERN.split(text)
        chunks = []
        for seg in segments:
            s = seg.strip()
            if not s:
                continue
            if len(s) <= max_chars:
                chunks.append(s)
            else:
                chunks.extend(_chunk_by_sentence(s, max_chars))
        if chunks:
            return chunks

    return _chunk_by_sentence(text, max_chars)
