FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY config/ config/
COPY app/ app/

# Qdrant host will be set via docker-compose (qdrant service)
ENV QDRANT_HOST=qdrant
ENV QDRANT_PORT=6333

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
