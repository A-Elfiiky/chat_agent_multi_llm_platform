# Runbook: Customer Service Platform

## 1. System Overview
The platform consists of 4 main microservices:
- **Gateway API**: Entry point (Port 8000)
- **Chat Orchestrator**: RAG & LLM Logic (Port 8002)
- **Ingestion Indexer**: Vector DB & Search (Port 8001)
- **Email/Voice**: Background workers

## 2. Deployment
### Local Development
```bash
python run_local.py
```

### Docker Production
```bash
docker-compose -f infra/docker-compose.yml up -d --build
```

## 3. Configuration
Edit `config.yaml` to update:
- API Keys (Grok, Gemini, etc.)
- Confidence Thresholds
- Feature Flags

## 4. Common Operational Tasks

### 4.1. Updating FAQs
1. Prepare a JSON file matching the schema in `data/faqs/sample_faq.json`.
2. Use the Admin Console (`clients/admin-console/index.html`) to upload.
3. Or use the API:
   ```bash
   curl -X POST http://localhost:8001/ingest -H "Content-Type: application/json" -d '{"file_path": "/abs/path/to/faqs.json"}'
   ```

### 4.2. Rotating API Keys
1. Update the environment variables or `config.yaml`.
2. Restart the `chat-orchestrator` service.

### 4.3. Handling "LLM Unavailable" Alerts
1. Check `docker logs chat-orchestrator`.
2. Verify internet connectivity.
3. Check status of configured providers (Grok, Gemini).
4. If all fail, the system automatically falls back to rule-based responses.

## 5. Troubleshooting

### Issue: "I don't have enough information" responses are too frequent.
- **Cause**: Retrieval score is below threshold (0.35).
- **Fix**: 
    1. Check if the question is covered in FAQs.
    2. Lower `rag.confidence_threshold` in `config.yaml` (risk of hallucination).
    3. Add more synonyms/keywords to FAQ content.

### Issue: High Latency (> 5s)
- **Cause**: LLM provider slowness or timeout.
- **Fix**: 
    1. Check Grafana dashboards for provider latency.
    2. Reorder `llm.fallback_order` in `config.yaml` to prioritize faster providers.

## 6. Security Procedures
- **PII Redaction**: Enabled by default. To modify patterns, edit `services/shared/security.py`.
- **Access Control**: Ensure `config.yaml` is not committed with real keys. Use Vault in production.
