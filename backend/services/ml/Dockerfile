FROM python:3.11-slim

WORKDIR /app

COPY services/ml/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY shared/ shared/
COPY services/ml/ services/ml/
COPY services/rag/ services/rag/
RUN touch /app/services/__init__.py

ENV PYTHONPATH=/app
EXPOSE 8005

CMD ["uvicorn", "services.ml.app.main:app", "--host", "0.0.0.0", "--port", "8005"]
