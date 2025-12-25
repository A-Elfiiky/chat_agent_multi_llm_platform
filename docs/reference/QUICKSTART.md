# Quick Start Guide

## 🚀 Your Platform is Running!

All services are now operational:

- **Gateway API**: http://localhost:8000
- **Chat Service**: http://localhost:8002  
- **Ingestion Service**: http://localhost:8001
- **Voice Service**: http://localhost:8004
- **Email Worker**: Running in background

## 📱 Try the Interfaces

### 1. Web Chat Widget
Open in browser: `clients/web-widget/index.html`

- Ask: "What is your return policy?"
- Ask: "How do I reset my password?"
- View citations and confidence scores

### 2. Admin Console  
Open in browser: `clients/admin-console/index.html`

- View system stats (interactions, latency)
- Test retrieval accuracy
- Monitor logs
- Upload new FAQ documents

### 3. API Documentation
http://localhost:8000/docs

- Interactive Swagger UI
- Test endpoints directly
- View request/response schemas

## 🧪 Testing the System

### Test Chat API (PowerShell)
```powershell
$body = @{
    message = "What is your return policy?"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"; "X-API-Key"="secret-client-key-123"} `
    -Body $body
```

### Test Voice Webhook (TwiML)
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/voice/webhook" -Method POST
```

### Test Search
```powershell
$body = @{
    query = "returns"
    k = 3
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8001/search" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"} `
    -Body $body
```

## 📊 What's Working

✅ **RAG Pipeline**: Documents indexed in FAISS, semantic search operational  
✅ **Multi-LLM Fallback**: OpenAI → Anthropic → Cohere (with Circuit Breakers)  
✅ **Voice IVR**: Twilio-compatible webhook with speech gathering  
✅ **Email Auto-Reply**: IMAP monitoring + RAG-based responses  
✅ **Admin Dashboard**: Real-time stats and log viewer  
✅ **API Security**: Key-based authentication  

## ⚠️ Known Limitations (Prototype)

- **Email**: Currently using dummy IMAP credentials (update `config.yaml` for real email)
- **Voice**: Mock ASR/TTS (connect real Twilio account for production)
- **LLM Providers**: Using mock responses (add real API keys in `config.yaml`)
- **Database**: SQLite for local dev (use PostgreSQL for production)

## 🔧 Configuration

Edit `config.yaml` to customize:
- LLM provider API keys
- Email credentials (IMAP/SMTP)
- Voice provider settings
- Database paths
- Logging levels

## 🛑 Stopping the Platform

Press `Ctrl+C` in the terminal running `run_local.py`

## 📚 Next Steps

1. **Add Real API Keys**: Update `config.yaml` with your LLM provider keys
2. **Connect Email**: Add real IMAP/SMTP credentials for email automation
3. **Test Voice**: Configure Twilio webhook to point to your Voice service
4. **Load More Data**: Upload additional FAQ documents via Admin Console
5. **Monitor**: Watch logs and metrics in Admin Console

---

**Need Help?** Check the API docs at http://localhost:8000/docs or review the service logs in the terminal.
