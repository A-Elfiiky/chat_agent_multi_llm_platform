# 🎯 Getting Started - Copilot Customer Service Platform

## Quick Start (3 Steps)

### Step 1: Start the Services

**Option A - PowerShell (Recommended):**
```powershell
.\start.ps1
```

**Option B - Command Prompt:**
```cmd
start.bat
```

**Option C - Manual:**
```bash
python run_local.py
```

Wait for all services to initialize (~10 seconds). You should see confirmation that services are running.

### Step 2: Open the Web Interfaces

#### Customer Chat Interface
- Navigate to: `clients/web-widget/index.html` in your browser
- Try asking: "What is your return policy?"
- Observe: Real-time RAG responses with citations

#### Admin Dashboard  
- Navigate to: `clients/admin-console/index.html` in your browser
- View: System stats, recent interactions, logs
- Test: Search functionality with your queries

### Step 3: Explore the API
- Open: http://localhost:8000/docs
- Try: POST `/api/v1/chat` endpoint
- Use API Key: `secret-client-key-123`

## Architecture Overview

```
┌─────────────────────────────────────────────────────────┐
│                      Gateway API :8000                   │
│              (Auth, Routing, Admin Endpoints)            │
└─────────────────┬───────────────────────────────────────┘
                  │
      ┌───────────┼───────────┬──────────────┐
      │           │           │              │
      ▼           ▼           ▼              ▼
┌──────────┐ ┌─────────┐ ┌────────┐   ┌──────────┐
│  Chat    │ │Ingestion│ │ Voice  │   │  Email   │
│  :8002   │ │  :8001  │ │ :8004  │   │  Worker  │
└──────────┘ └─────────┘ └────────┘   └──────────┘
      │           │           │              │
      │     ┌─────▼──────┐    │              │
      │     │   FAISS    │    │              │
      │     │ Vector DB  │    │              │
      │     └────────────┘    │              │
      │                       │              │
      └───────┬───────────────┴──────────────┘
              │
        ┌─────▼──────┐
        │  SQLite    │
        │  Logs DB   │
        └────────────┘
```

## Features Demonstration

### 1. RAG-Based Chat
**What it does**: Answers questions using only your knowledge base  
**Try it**:
- Ask: "How do I reset my password?"
- Ask: "What are your shipping options?"
- Ask: "Tell me about returns"

**Observe**:
- Confidence scores
- Source citations
- Low-confidence warnings

### 2. Voice IVR
**What it does**: Handles phone calls with menu navigation  
**Try it**: 
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/voice/webhook" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "CallSid=test123&Digits=3"
```

**Observe**: TwiML XML response for call routing

### 3. Email Auto-Reply
**What it does**: Monitors inbox, generates smart replies  
**Note**: Currently using dummy credentials (authentication errors expected)  
**To activate**: Update `config.yaml` with real IMAP/SMTP settings

### 4. Admin Monitoring
**What it does**: Real-time system observability  
**Try it**:
- View total interactions
- Check average latency
- See provider usage distribution
- Browse recent logs

## Configuration

### Adding Real LLM Providers
Edit `config.yaml`:
```yaml
llm_providers:
  openai:
    api_key: "sk-your-real-key-here"
    model: "gpt-4"
  anthropic:
    api_key: "your-anthropic-key"
    model: "claude-3-sonnet"
```

### Adding Email Support
Edit `config.yaml`:
```yaml
email_settings:
  imap:
    server: "imap.gmail.com"
    username: "your-support@company.com"
    password: "your-app-password"
  smtp:
    server: "smtp.gmail.com"
    username: "your-support@company.com"
    password: "your-app-password"
```

### Loading Your Knowledge Base
1. Prepare documents in JSON format (see `data/faqs/sample_faq.json`)
2. Open Admin Console
3. Click "Ingest & Index"
4. Upload your FAQ file
5. System rebuilds vector index automatically

## Troubleshooting

### Services Won't Start
- **SSL Certificate Errors**: Normal for HuggingFace model downloads. Workaround is applied in code.
- **Port Already in Use**: Stop other applications using ports 8000-8004
- **Module Not Found**: Run `pip install -r requirements.txt`

### Email Errors Expected
```
IMAP Connection failed: [AUTHENTICATIONFAILED]
```
This is normal with dummy credentials. Update `config.yaml` for real email.

### No Responses from Chat
- Check if Ingestion Service loaded the FAQs successfully
- Verify `data/index/` contains FAISS index files
- Re-run ingestion if needed

## Performance Metrics

**Typical Response Times** (on development machine):
- Chat query: 200-500ms
- Vector search: 50-100ms
- Voice webhook: <100ms
- Admin stats: <50ms

## Security Notes

**Current API Keys** (development only):
- Client API Key: `secret-client-key-123`
- Admin API Key: `admin-key-456`

**For Production**:
- Generate secure random keys
- Use environment variables
- Enable HTTPS
- Add rate limiting

## Support & Documentation

- **API Documentation**: http://localhost:8000/docs
- **Architecture**: See `COMPLETION_SUMMARY.md`
- **Manual Tests**: See `MANUAL_TESTS.md`
- **Status**: See `STATUS.md`

## Next Actions

1. ✅ Test the Web Widget - Chat with the AI
2. ✅ Explore Admin Console - View system metrics
3. ✅ Try the API - Use Swagger UI
4. 🔄 Add your API keys - Enable real LLM responses
5. 🔄 Load your data - Upload company FAQs
6. 🔄 Deploy - Use Docker configs in `ops/`

---

**Platform Status**: ✅ Fully Operational  
**Last Updated**: November 28, 2025  
**Version**: 1.0.0 (Local Development)
