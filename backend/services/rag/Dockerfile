FROM python:3.11-slim

WORKDIR /app

COPY services/rag/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ shared/
COPY services/rag/ services/rag/
COPY services/safeguard/ services/safeguard/
# Reranker lives in shared/reranker/ (already copied above). No services/reranker/.
# Ensure "services" is a proper package so "services.rag.app.main" resolves (same as local PYTHONPATH=backend)
RUN mkdir -p /app/services && touch /app/services/__init__.py

# Pre-download BGE reranker (~1.1 GB) so the container does not need to download at
# runtime (avoids "no space left on device" when the container has limited disk).
RUN python -c "from sentence_transformers import CrossEncoder; CrossEncoder('BAAI/bge-reranker-base')"

ENV PYTHONPATH=/app
EXPOSE 8004

CMD ["uvicorn", "services.rag.app.main:app", "--host", "0.0.0.0", "--port", "8004"]
