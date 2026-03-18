"""Tests for chunker module."""

from shared.chunker import chunk_text


def test_chunk_text_respects_sentence_boundaries():
    """Chunks should not split mid-sentence."""
    text = "First sentence. Second sentence. Third sentence."
    chunks = chunk_text(text, max_chars=50)
    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.endswith(".") or chunk.endswith("?") or chunk.endswith("!")


def test_chunk_text_small_text_returns_single_chunk():
    """Short text should produce one chunk."""
    text = "Short."
    chunks = chunk_text(text, max_chars=800)
    assert len(chunks) == 1
    assert chunks[0] == "Short."


def test_chunk_text_splits_qa_pairs():
    """Q&A-style text should be split per Question/Answer pair."""
    text = (
        "Question: Who is Mili? Answer: Mili is a Senior Software Developer.\n"
        "Question: What is Mili's tech stack? Answer: React, Node, AWS.\n"
        "Question: What is ACL? Answer: Access Control List."
    )
    chunks = chunk_text(text, max_chars=800)
    assert len(chunks) == 3
    assert "Who is Mili" in chunks[0] and "Senior Software Developer" in chunks[0]
    assert "tech stack" in chunks[1] and "React" in chunks[1]
    assert "ACL" in chunks[2] and "Access Control List" in chunks[2]
