# 🚀 Installation & Setup Guide

Complete guide for setting up the AI Customer Service Platform with all features.

---

## 📋 Prerequisites

### Required
- **Python 3.10+** (Download from [python.org](https://python.org))
- **PowerShell 5.1+** (Built into Windows)
- **Git** (Optional, for cloning)

### Recommended
- **Docker Desktop** (For Qdrant vector database)
- **8GB RAM** minimum
- **10GB free disk space**

---

## ⚡ Quick Install (5 Minutes)

### Step 1: Install Dependencies
```powershell
cd "c:\ahmed adel\Personal\projects\copilot"
pip install -r requirements.txt
```

### Step 2: Install Translation Library (Optional but Recommended)
```powershell
pip install googletrans==4.0.0-rc1
```

**Note:** Translation works without this library using pattern matching, but installing it provides better accuracy and more features.

### Step 3: Start the Platform
```powershell
.\start.ps1
```

This automatically starts:
- Qdrant vector database (Port 6333)
- RAG Ingestion Service (Port 8002)
- Chat Orchestrator (Port 8001)
- Gateway API (Port 8000)

### Step 4: Verify Installation
```powershell
.\status.ps1
```

You should see all services running ✅

---

## 🧪 Test the Installation

### Run Automated Tests
```powershell
.\test-features.ps1
```

This tests:
- ✅ Multi-language translation (Spanish, French, German, Italian)
- ✅ Sentiment analysis & escalation
- ✅ Analytics dashboard
- ✅ Rate limiting
- ✅ Knowledge gap detection
- ✅ Translation caching
- ✅ Performance metrics
- ✅ Cost analysis

### Run Interactive Demo
```powershell
.\demo.ps1
```

This demonstrates:
- 🌍 Multi-language customer support scenarios
- 😊 Sentiment-based escalation
- 📊 Real-time analytics
- 💰 Cost optimization
- 🎓 Knowledge base learning

---

## 🔧 Manual Installation (Advanced)

### 1. Clone Repository (if applicable)
```powershell
git clone <your-repo-url>
cd copilot
```

### 2. Create Virtual Environment (Recommended)
```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 3. Install Core Dependencies
```powershell
pip install fastapi uvicorn pydantic
pip install openai anthropic google-generativeai
pip install qdrant-client
pip install python-multipart aiofiles
pip install pyyaml
```

### 4. Install Optional Dependencies

#### Translation Support
```powershell
# Option 1: googletrans (Recommended - Free)
pip install googletrans==4.0.0-rc1

# Option 2: deep-translator (Alternative)
pip install deep-translator
```

#### Additional Features
```powershell
# For enhanced analytics
pip install pandas numpy

# For advanced sentiment analysis
pip install textblob
```

### 5. Configure Environment Variables (Optional)

Create `.env` file:
```env
# LLM Provider API Keys
OPENAI_API_KEY=your-openai-key
ANTHROPIC_API_KEY=your-anthropic-key
GOOGLE_API_KEY=your-google-key

# Translation API (if using Google Translate API)
GOOGLE_TRANSLATE_API_KEY=your-translate-key

# Database
DATABASE_PATH=data/copilot.db

# Rate Limits (optional, has defaults)
RATE_LIMIT_PER_MINUTE=20
RATE_LIMIT_PER_HOUR=500
RATE_LIMIT_PER_DAY=5000
```

### 6. Initialize Database
```powershell
python -c "from services.shared.conversation_memory import ConversationMemory; ConversationMemory()"
```

### 7. Start Services Individually

#### Terminal 1: Start Qdrant
```powershell
docker run -p 6333:6333 qdrant/qdrant
```

#### Terminal 2: Start RAG Service
```powershell
cd services/rag-ingestion
python main.py
```

#### Terminal 3: Start Chat Orchestrator
```powershell
cd services/chat-orchestrator
python main.py
```

#### Terminal 4: Start Gateway API
```powershell
cd services/gateway-api
python main.py
```

---

## 🔍 Troubleshooting

### Issue: "Translation library not found"

**Solution:**
```powershell
pip install googletrans==4.0.0-rc1
```

Or the system will use pattern-matching fallback (still works, just less accurate).

---

### Issue: "Port already in use"

**Solution:**
```powershell
# Stop existing services
.\stop.ps1

# Wait 5 seconds
Start-Sleep -Seconds 5

# Restart
.\start.ps1
```

Or change ports in `config.yaml`.

---

### Issue: "Qdrant connection failed"

**Solution 1 - Docker:**
```powershell
docker ps  # Check if Qdrant is running
docker run -p 6333:6333 qdrant/qdrant  # Start Qdrant
```

**Solution 2 - Local Qdrant:**
Download from [qdrant.tech](https://qdrant.tech) and run locally.

---

### Issue: "Module not found" errors

**Solution:**
```powershell
# Reinstall all dependencies
pip install -r requirements.txt --force-reinstall
```

---

### Issue: "Database locked" error

**Solution:**
```powershell
# Stop all services
.\stop.ps1

# Delete lock file (if exists)
Remove-Item data/copilot.db-journal -ErrorAction SilentlyContinue

# Restart
.\start.ps1
```

---

### Issue: Low cache hit rate

**Cause:** System needs time to build cache.

**Solution:**
- Let system run for a few hours
- Check cache stats: `curl http://localhost:8000/admin/analytics/dashboard`
- Typical hit rate: 60-80% after warm-up period

---

## 📊 Verify Installation

### Check Service Health
```powershell
# Gateway API
curl http://localhost:8000/health

# Chat Orchestrator
curl http://localhost:8001/health

# RAG Ingestion
curl http://localhost:8002/health

# Qdrant
curl http://localhost:6333/collections
```

### Test Chat Endpoint
```powershell
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"Hello, how can I help?\", \"session_id\": \"test-123\"}'
```

### Test Multi-language
```powershell
# Spanish
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"¿Dónde está mi pedido?\", \"session_id\": \"test-es\"}'

# French  
curl -X POST http://localhost:8000/chat `
  -H "Content-Type: application/json" `
  -d '{\"message\": \"Comment puis-je suivre ma commande?\", \"session_id\": \"test-fr\"}'
```

### Check Analytics
```powershell
curl http://localhost:8000/admin/analytics/dashboard?days=7
curl http://localhost:8000/admin/translation/stats
curl http://localhost:8000/admin/rate-limits/stats
```

---

## 🎨 Admin Console Setup

### Option 1: Local File
1. Navigate to `clients/admin-console/`
2. Open `index-advanced.html` in your browser
3. Dashboard loads automatically

### Option 2: Web Server (Optional)
```powershell
cd clients/admin-console
python -m http.server 8080
```

Then open: http://localhost:8080/index-advanced.html

---

## 🔐 Security Setup (Production)

### 1. Generate API Keys
```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### 2. Configure Rate Limits
Edit `services/shared/rate_limiter.py`:
```python
DEFAULT_LIMITS = {
    'per_minute': 20,
    'per_hour': 500,
    'per_day': 5000
}
```

### 3. Enable HTTPS (Production)
Use nginx or similar reverse proxy:
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;
    
    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### 4. Database Backup
```powershell
# Backup database
Copy-Item data/copilot.db data/backups/copilot-$(Get-Date -Format 'yyyy-MM-dd').db

# Schedule automatic backups (Windows Task Scheduler)
schtasks /create /tn "Copilot DB Backup" /tr "powershell Copy-Item data/copilot.db data/backups/copilot-$(Get-Date -Format 'yyyy-MM-dd').db" /sc daily /st 02:00
```

---

## 📈 Performance Tuning

### Increase Cache TTL
Edit `services/chat-orchestrator/main.py`:
```python
cache = ResponseCache(ttl_hours=48)  # 48 hours instead of 24
```

### Adjust Rate Limits
Edit `services/shared/rate_limiter.py`:
```python
DEFAULT_LIMITS = {
    'per_minute': 50,    # Increased from 20
    'per_hour': 1000,    # Increased from 500
    'per_day': 10000     # Increased from 5000
}
```

### Database Optimization
```sql
-- Run these on SQLite database for better performance
PRAGMA journal_mode=WAL;
PRAGMA synchronous=NORMAL;
PRAGMA cache_size=10000;
PRAGMA temp_store=MEMORY;
```

---

## 🚀 Production Deployment

### Docker Deployment (Recommended)

Create `Dockerfile`:
```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
RUN pip install googletrans==4.0.0-rc1

COPY . .

EXPOSE 8000

CMD ["python", "run_local.py"]
```

Build and run:
```powershell
docker build -t copilot-platform .
docker run -p 8000:8000 copilot-platform
```

### Cloud Deployment

#### AWS
- Use EC2 instance (t3.medium or larger)
- Set up Application Load Balancer
- Use RDS for PostgreSQL (upgrade from SQLite)
- CloudWatch for monitoring

#### Azure
- App Service for hosting
- Azure Database for PostgreSQL
- Application Insights for analytics

#### Google Cloud
- Cloud Run for containers
- Cloud SQL for database
- Cloud Monitoring

---

## 📚 Next Steps

1. **Read Documentation:**
   - `PROJECT_SUMMARY.md` - Complete overview
   - `QUICK_REFERENCE.md` - API examples
   - `TRANSLATION_SETUP.md` - Language setup

2. **Run Tests:**
   ```powershell
   .\test-features.ps1
   ```

3. **Run Demo:**
   ```powershell
   .\demo.ps1
   ```

4. **Open Admin Console:**
   - Navigate to `clients/admin-console/index-advanced.html`

5. **Monitor Analytics:**
   - Check dashboard regularly
   - Review knowledge gaps weekly
   - Approve FAQ suggestions

6. **Optimize Costs:**
   - Monitor cache hit rates
   - Review cost analysis monthly
   - Clean old cache entries

---

## ✅ Installation Checklist

- [ ] Python 3.10+ installed
- [ ] Dependencies installed (`pip install -r requirements.txt`)
- [ ] Translation library installed (`pip install googletrans==4.0.0-rc1`)
- [ ] Services started (`.\start.ps1`)
- [ ] Services verified (`.\status.ps1`)
- [ ] Tests passed (`.\test-features.ps1`)
- [ ] Demo works (`.\demo.ps1`)
- [ ] Admin console accessible
- [ ] Analytics dashboard shows data
- [ ] Multi-language translation working
- [ ] Rate limiting functional
- [ ] Knowledge gap detection active

---

**Installation Complete! 🎉**

Your AI Customer Service Platform is ready for production use with all 8 features fully operational.
