FROM python:3.9-slim

WORKDIR /app

COPY services/email-responder/requirements.txt .
# If requirements.txt doesn't exist, create a dummy one or skip
RUN pip install --no-cache-dir requests pyyaml

COPY . .

ENV PYTHONPATH=/app
