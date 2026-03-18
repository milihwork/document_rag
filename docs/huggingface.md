# Hugging Face (Embedding Backend)

This project uses **Hugging Face** via the [sentence-transformers](https://www.sbert.net/) library for **local text embeddings**. No API key is required when using public models; everything runs on your machine.

## Role in the Stack

| Component | Usage |
|-----------|--------|
| **Embedding service** | `EMBEDDING_BACKEND=huggingface` (or alias `local`) loads a sentence-transformers model and exposes `POST /embed` for single and batch embedding. |
| **Models** | Models are downloaded from the [Hugging Face Hub](https://huggingface.co/models) on first use and cached locally. |

The RAG pipeline uses these embeddings to index document chunks and to embed user queries for vector search. The same backend is used for both ingestion and query-time embedding.

## Configuration

### Backend selection

Set the embedding backend to Hugging Face (recommended explicit name) or the legacy alias:

```bash
EMBEDDING_BACKEND=huggingface   # or local
```

### Required

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_MODEL` | `BAAI/bge-small-en-v1.5` | Hugging Face model id (e.g. `author/repo`). Used for both single and batch embedding. |

### Optional

| Variable | Default | Description |
|----------|---------|-------------|
| `EMBEDDING_NORMALIZE` | `true` | Normalize embeddings (recommended for cosine similarity). Changing this or the model requires re-embedding existing vectors. |
| `EMBEDDING_DEVICE` | (auto) | Device for inference: e.g. `cpu`, `cuda`, `mps`. Leave unset to let sentence-transformers choose. |
| `EMBEDDING_BATCH_SIZE` | `32` | Batch size for `embed_batch`. Tune for your GPU/CPU memory. |
| `EMBEDDING_MAX_LENGTH` | (model default) | Max token length for inputs. Set to truncate long texts (e.g. `512`). |

Example `.env` snippet:

```bash
EMBEDDING_BACKEND=huggingface
EMBEDDING_MODEL=BAAI/bge-small-en-v1.5
EMBEDDING_NORMALIZE=true
# EMBEDDING_DEVICE=cpu
# EMBEDDING_BATCH_SIZE=32
# EMBEDDING_MAX_LENGTH=512
```

## Model choice

- **Default:** `BAAI/bge-small-en-v1.5` — good balance of quality and speed for English; 384-dimensional embeddings.
- **Alternatives (Hugging Face Hub):**
  - Larger English: e.g. `BAAI/bge-base-en-v1.5`, `BAAI/bge-large-en-v1.5` (higher quality, more compute).
  - Multilingual: e.g. `BAAI/bge-m3`, `sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2`.
  - Other: search [Hugging Face — sentence-transformers](https://huggingface.co/models?library=sentence-transformers) and set `EMBEDDING_MODEL` to the model id.

**Important:** If you change `EMBEDDING_MODEL` or `EMBEDDING_NORMALIZE`, existing vectors in the vector store were produced with different settings. Re-run ingestion so all embeddings are consistent.

## Caching and offline use

- **Cache:** Models are stored under the Hugging Face cache (e.g. `~/.cache/huggingface/hub`). After the first run, the same model loads from disk without re-downloading.
- **Offline:** To run without network, download the model once while online, then set `HF_HUB_OFFLINE=1` (or use [Offline mode](https://huggingface.co/docs/huggingface_hub/guides/offline)) so the library uses only the cache.

## Gated / private models

For gated models (e.g. some Llama or custom private models):

1. Log in via CLI: `huggingface-cli login` and enter your [Hugging Face token](https://huggingface.co/settings/tokens).
2. Or set `HF_TOKEN` (or `HUGGING_FACE_HUB_TOKEN`) in the environment where the embedding service runs.

The embedding service uses `sentence_transformers`, which relies on `huggingface_hub` for downloads; that client will use the token when the model is gated.

## Implementation details

- **Code:** `backend/services/embedding/app/backends/local.py` — `LocalEmbeddingBackend` and `HuggingFaceEmbeddingBackend` (alias).
- **Contract:** `embed(text: str) -> list[float]` and `embed_batch(texts: list[str]) -> list[list[float]]`; same as other embedding backends (see [Backends](backends.md)).
- **Dependencies:** `sentence-transformers` (and its Hugging Face dependencies) in `backend/services/embedding/requirements.txt`.

## See also

- [Backends](backends.md) — adding and switching embedding/vector/LLM backends.
- [Architecture](architecture.md) — how the embedding service fits in the RAG pipeline.
- [Hugging Face — sentence-transformers models](https://huggingface.co/models?library=sentence-transformers)
- [sentence-transformers documentation](https://www.sbert.net/)
