FROM python:3.9-slim

WORKDIR /app

COPY services/ingestion-indexer/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
