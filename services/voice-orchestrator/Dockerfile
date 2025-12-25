FROM python:3.9-slim

WORKDIR /app

COPY services/voice-orchestrator/requirements.txt .
# If requirements.txt doesn't exist, create a dummy one or skip
# For now, we'll assume it exists or we install common libs
RUN pip install --no-cache-dir fastapi uvicorn pydantic pyyaml

COPY . .

ENV PYTHONPATH=/app
