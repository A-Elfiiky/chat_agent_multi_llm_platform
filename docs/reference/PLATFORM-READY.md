# 🎉 Platform Ready - Quick Start Guide

## ✅ System Status

Your Copilot Platform is now **fully operational** with:

- ✅ **Groq LLM Provider** - Working with `llama-3.1-8b-instant` model
- ✅ **RAG/Vector Search** - FAISS index retrieving relevant context
- ✅ **Gateway API** - Handling requests with authentication
- ✅ **Chat Orchestrator** - Routing queries to LLM with RAG
- ✅ **Voice Orchestrator** - Ready for Twilio integration
- ✅ **Email Responder** - Queue-based email processing

---

## 🚀 Starting the Platform

### Option 1: PowerShell Script (Recommended)
```powershell
powershell -ExecutionPolicy Bypass -File start.ps1
```

### Option 2: Python Directly
```powershell
& .\.venv\Scripts\python.exe scripts\run_local.py
```

### Stopping the Platform
```powershell
powershell -ExecutionPolicy Bypass -File stop.ps1
```

---

## 💬 Testing the Chat Endpoint

### Using PowerShell

```powershell
$headers = @{
    'Content-Type' = 'application/json'
    'X-API-Key' = 'secret-client-key-123'
}

$body = @{
    user_id = "test-user"
    message = "How do I reset my password?"
    language = "en"
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/chat' `
    -Method POST `
    -Headers $headers `
    -Body $body | 
    Select-Object -ExpandProperty Content | 
    ConvertFrom-Json | 
    ConvertTo-Json -Depth 5
```

### Using curl
```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -H "X-API-Key: secret-client-key-123" \
  -d '{"user_id":"test","message":"How do I reset my password?","language":"en"}'
```

### Valid API Keys
From `config.yaml`:
- `secret-client-key-123` (client key)
- `admin-key-456` (admin key)

---

## 📞 Voice Calling Setup

### Prerequisites
1. **Twilio Account** - Sign up at https://www.twilio.com
2. **ngrok** - Download from https://ngrok.com

### Step 1: Get Your Twilio Credentials

1. Log in to Twilio Console: https://console.twilio.com
2. Get your **Account SID** and **Auth Token** from the dashboard
3. Buy a phone number (or use trial number)

Update `.env`:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+1234567890
```

### Step 2: Start ngrok Tunnel

```powershell
ngrok http 8004
```

You'll see output like:
```
Forwarding  https://abc123.ngrok.io -> http://localhost:8004
```

Copy the `https://` URL (e.g., `https://abc123.ngrok.io`)

### Step 3: Configure Twilio Webhook

1. Go to Twilio Console → Phone Numbers → Your number
2. Under "Voice & Fax", set:
   - **A CALL COMES IN**: Webhook
   - **URL**: `https://abc123.ngrok.io/voice/inbound` (your ngrok URL + `/voice/inbound`)
   - **HTTP**: POST
3. Click Save

### Step 4: Test Inbound Call

Call your Twilio number! The flow:
1. Caller dials your Twilio number
2. Twilio → ngrok → Voice Orchestrator (localhost:8004)
3. Voice Orchestrator responds with TwiML
4. Caller hears greeting and can speak

### Step 5: Make Outbound Call (Optional)

```powershell
$headers = @{
    'Content-Type' = 'application/json'
    'X-API-Key' = 'secret-client-key-123'
}

$body = @{
    to_number = "+1234567890"  # Recipient's phone
    from_number = "+0987654321"  # Your Twilio number
    message = "Hello! This is a test call from your AI assistant."
} | ConvertTo-Json

Invoke-WebRequest -Uri 'http://localhost:8000/voice/outbound' `
    -Method POST `
    -Headers $headers `
    -Body $body
```

---

## 🌐 Web Clients

### Admin Console
Open in browser:
```
file:///C:/ahmed%20adel/Personal/projects/copilot/clients/admin-console/index.html
```

Or use:
```
clients/admin-console/index.html
```

Features:
- System configuration
- Analytics dashboard
- User management
- Model selection

### Web Widget
Open in browser:
```
file:///C:/ahmed%20adel/Personal/projects/copilot/clients/web-widget/index.html
```

Or embed in your website:
```html
<iframe src="http://localhost:8000/widget" width="400" height="600"></iframe>
```

---

## 🔑 API Endpoints

All endpoints require `X-API-Key` header.

### Health Check
```
GET http://localhost:8000/health
```

### Chat
```
POST http://localhost:8000/chat
{
  "user_id": "string",
  "message": "string",
  "language": "en"
}
```

### Voice Inbound
```
POST http://localhost:8004/voice/inbound
(Called by Twilio, returns TwiML)
```

### Voice Outbound
```
POST http://localhost:8000/voice/outbound
{
  "to_number": "+1234567890",
  "from_number": "+0987654321",
  "message": "Your message"
}
```

### Email
```
POST http://localhost:8000/email/send
{
  "to": "user@example.com",
  "subject": "Your Subject",
  "body": "Your message"
}
```

---

## 🔧 Configuration

### LLM Providers
Edit `config.yaml`:

```yaml
llm:
  fallback_order:
    - "grok"    # Not configured (API unreachable)
    - "groq"    # ✅ WORKING (llama-3.1-8b-instant)
    - "gemini"  # Configured but returns 404
    - "local"   # Not running
  
  providers:
    groq:
      api_key_env: "GROQ_API_KEY"
      model: "llama-3.1-8b-instant"
```

### Available Groq Models
- `llama-3.1-8b-instant` ✅ (currently used - fast and reliable)
- `llama-3.1-70b-versatile` (more capable but slower)
- `mixtral-8x7b-32768` (good for long contexts)

To switch models, edit `config.yaml` and restart:
```powershell
powershell -ExecutionPolicy Bypass -File stop.ps1
powershell -ExecutionPolicy Bypass -File start.ps1
```

### Environment Variables
Edit `.env` file in project root:

```env
# Groq LLM (WORKING)
GROQ_API_KEY=gsk_b9RMYaCILi00k7xV...

# Google Gemini (configured but needs fixing)
GEMINI_KEY=AIzaSyCWLDTNOxlj3eal...

# Twilio Voice (for voice calls)
TWILIO_ACCOUNT_SID=ACxxxx...
TWILIO_AUTH_TOKEN=your_token
TWILIO_PHONE_NUMBER=+1234567890

# Supabase (database)
SUPABASE_URL=https://...
SUPABASE_KEY=eyJhbG...
```

---

## 📊 Service Ports

| Service | Port | Purpose |
|---------|------|---------|
| Gateway API | 8000 | Main entry point |
| Ingestion Indexer | 8001 | Document processing |
| Chat Orchestrator | 8002 | LLM + RAG logic |
| Voice Orchestrator | 8004 | Twilio webhooks |
| Email Responder | 8005 | Email processing |

---

## 🐛 Troubleshooting

### "I'm currently unavailable" responses
This was the original issue - **now fixed!** The problem was:
1. Environment variables not propagating to services
2. Incorrect Groq model name
3. Services needed restart to load new config

**Solution applied:**
- ✅ Added `env=os.environ.copy()` to `scripts/run_local.py`
- ✅ Changed model to `llama-3.1-8b-instant`
- ✅ Restarted all services

### Services won't start
```powershell
# Check Python processes
Get-Process python

# Kill all and restart
powershell -ExecutionPolicy Bypass -File stop.ps1
powershell -ExecutionPolicy Bypass -File start.ps1
```

### Voice calls not working
1. Check ngrok is running: `ngrok http 8004`
2. Verify Twilio webhook URL matches ngrok URL
3. Check Voice Orchestrator is up: `curl http://localhost:8004/health`
4. Check `.env` has correct Twilio credentials

### Chat returns 401 Unauthorized
Add `X-API-Key` header with valid key from `config.yaml`:
- `secret-client-key-123`
- `admin-key-456`

### Chat returns wrong field error
Use `message` not `question`:
```json
{
  "user_id": "test",
  "message": "Your question here",  // ✅ Correct
  "language": "en"
}
```

---

## 📚 Documentation

- **Architecture**: `docs/ARCHITECTURE.md`
- **Voice Setup**: `docs/reference/VOICE-CALLS.md`
- **Admin Console**: `clients/admin-console/CONTROL-CENTER-README.md`
- **Quick Start**: `docs/reference/QUICK_REFERENCE.md`

---

## ✨ What's Working Now

### ✅ Completed
1. **Groq LLM Integration** - Real AI responses powered by LLaMA 3.1
2. **RAG System** - FAISS vector search retrieving relevant FAQs
3. **API Gateway** - Authentication and routing
4. **Environment Management** - `.env` file with API keys
5. **Service Orchestration** - `start.ps1`/`stop.ps1` scripts

### 🔄 Ready to Use
1. **Voice Calling** - Documented, needs Twilio account + ngrok
2. **Admin Console** - HTML interface for system management
3. **Web Widget** - Embeddable chat widget

### ⏳ Needs Configuration
1. **Gemini Provider** - Configured but getting 404 errors (model name issue)
2. **Grok Provider** - API endpoint unreachable
3. **Local LLM** - Not running (optional)

---

## 🎯 Next Steps

1. **Test Voice Calling**: Follow Step-by-Step guide above
2. **Fix Gemini** (optional): Try different model name or endpoint
3. **Add More FAQs**: Add JSON files to `data/faqs/`
4. **Customize Responses**: Edit system prompts in `config.yaml`
5. **Monitor Usage**: Check admin console analytics

---

## 🤝 Support

- **Logs**: Check terminal output where `start.ps1` ran
- **Health Checks**: `curl http://localhost:8000/health`
- **Test Script**: `python scripts/test_llm_direct.py`

---

**Platform Status**: 🟢 **OPERATIONAL**

Last updated: December 1, 2025
