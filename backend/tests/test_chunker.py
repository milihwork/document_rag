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
