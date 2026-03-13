FROM python:3.11-slim

WORKDIR /app

COPY services/retrieval/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ shared/
COPY services/retrieval/ services/retrieval/

ENV PYTHONPATH=/app
EXPOSE 8003

CMD ["uvicorn", "services.retrieval.app.main:app", "--host", "0.0.0.0", "--port", "8003"]
