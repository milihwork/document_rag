FROM python:3.11-slim

WORKDIR /app

COPY services/ingestion/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ shared/
COPY services/ingestion/ services/ingestion/

ENV PYTHONPATH=/app
EXPOSE 8001

CMD ["uvicorn", "services.ingestion.app.main:app", "--host", "0.0.0.0", "--port", "8001"]
