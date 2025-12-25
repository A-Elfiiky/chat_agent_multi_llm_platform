FROM python:3.9-slim

WORKDIR /app

COPY services/chat-orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PYTHONPATH=/app
