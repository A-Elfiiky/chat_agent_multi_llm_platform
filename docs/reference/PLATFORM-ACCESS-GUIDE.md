# 🚀 Platform Access & Testing Guide

## Quick Start (3 Steps)

### Step 1: Start the Backend Services
```powershell
.\launch.ps1
```

**What happens:**
- Backend services start on ports 8000-8004
- Takes 8-10 seconds to initialize
- You'll see "Ready to Go!" when complete

### Step 2: Open the Welcome Page
1. Navigate to your project folder: `C:\ahmed adel\Personal\projects\copilot`
2. Double-click `index.html`
3. Your browser will open the centralized welcome page

### Step 3: Access the Control Center
1. On the welcome page, click **"Open Control Center"** button
2. The full admin dashboard will open
3. Use the sidebar to navigate all 14 sections

---

## 🧪 Complete Testing Guide

### Test 1: Backend Health Check

**Method A - Browser:**
1. Open browser
2. Go to: http://localhost:8000/health
3. Should see: `{"status":"ok"}` or similar

**Method B - PowerShell:**
```powershell
.\status.ps1
```

**Expected Output:**
- Gateway API (8000): ✓ Running
- Chat Orchestrator (8002): ✓ Running
- Ingestion Service (8001): ✓ Running
- Voice Orchestrator (8004): ✓ Running

---

### Test 2: API Documentation

1. Open browser
2. Go to: http://localhost:8000/docs
3. You'll see **Swagger UI** with all API endpoints

**Try these endpoints:**
- `GET /health` - Click "Try it out" → "Execute"
- `POST /chat` - Send a test message
- `GET /admin/analytics/dashboard` - View analytics

---

### Test 3: Web Chat Widget (Customer Interface)

**Access:**
1. Open `clients/web-widget/index.html` in browser
2. Or click "Open Chat" from welcome page

**Test Scenarios:**

#### Basic Chat:
1. Type: "Hello, how can you help me?"
2. Click "Send"
3. Should get AI response with:
   - Answer text
   - Confidence score
   - Response time
   - Citations (if using RAG)

#### Multi-language Chat:
1. Select language from dropdown (e.g., Spanish, French, Arabic)
2. Type message in that language
3. Should get response in same language

#### Sentiment Detection:
1. Type: "I'm very frustrated with your service!"
2. Check response - should detect negative sentiment
3. May trigger escalation flag

---

### Test 4: Control Center Dashboard

**Access:** `clients/admin-console/control-center.html`

#### Dashboard Overview:
1. Click **"Dashboard"** in sidebar
2. View these stats:
   - Total Interactions
   - Cache Hit Rate
   - Avg Response Time
   - Escalation Rate
3. Check charts:
   - Traffic chart (line chart)
   - Sentiment distribution (donut chart)

#### Test Refresh:
1. Click **"Refresh"** button in header
2. Data should reload
3. Charts should update

---

### Test 5: Analytics Section

**Access:** Click **"Analytics"** in Control Center sidebar

**Tests:**

#### Daily Metrics:
1. View interactions per day chart
2. Check response times trend
3. Review cache performance

#### Export Data:
1. Click "Export Analytics" button
2. JSON file downloads with all metrics
3. Verify file contains data

---

### Test 6: Multi-language Translation

**Access:** Click **"Multi-language"** in sidebar

**Tests:**

#### Language Stats:
1. View supported languages list
2. Check translation counts
3. Review most used languages

#### Add Translation:
1. Scroll to "Manual Translations" section
2. Add English text
3. Add translation in another language
4. Click "Save"

---

### Test 7: Sentiment Analysis & Escalation

**Access:** Click **"Sentiment & Escalation"** in sidebar

**Tests:**

#### View Sentiment Stats:
1. Check sentiment distribution chart
2. View escalation rate
3. Review urgent cases table

#### Create Escalation:
1. Send angry message via chat widget
2. Return to Control Center
3. Should appear in escalations list
4. Can assign to agent

---

### Test 8: Response Caching

**Access:** Click **"Response Caching"** in sidebar

**Tests:**

#### View Cache Stats:
1. Check hit rate percentage
2. Review cached entries count
3. See cache savings

#### Test Cache:
1. Go to chat widget
2. Ask: "What are your hours?"
3. Ask same question again
4. Second response should be faster (cached)
5. Check cache stats - hit count increased

#### Clear Cache:
1. Click "Clear All Cache" button
2. Confirm action
3. Stats should reset

---

### Test 9: Rate Limiting

**Access:** Click **"Rate Limiting"** in sidebar

**Tests:**

#### View Rate Limits:
1. Check current limits per IP
2. Review blocked IPs
3. See rate limit violations

#### Test Rate Limit:
1. Go to chat widget
2. Send 20+ messages rapidly
3. Should get rate limit error
4. Check Control Center - violation logged

---

### Test 10: Knowledge Base

**Access:** Click **"Knowledge Base"** in sidebar

**Tests:**

#### View FAQs:
1. Check total FAQs count
2. Review most asked questions
3. See confidence scores

#### Add FAQ:
1. Click "Add FAQ" or "Upload Document"
2. Enter question and answer
3. Save
4. Test in chat widget by asking that question

#### Upload Document:
1. Click "Upload Document"
2. Select .txt, .pdf, or .docx file
3. Upload
4. System ingests and indexes content
5. Ask questions about document in chat

---

### Test 11: Conversations History

**Access:** Click **"Conversations"** in sidebar

**Tests:**

#### View Sessions:
1. See all chat sessions
2. Check session IDs
3. Review timestamps

#### View Conversation:
1. Click on a session
2. See full message history
3. View sentiment per message
4. Check response times

#### Export Conversation:
1. Select a session
2. Click "Export"
3. Download conversation log

---

### Test 12: Voice & Calling (IVR)

**Access:** Click **"Voice & Calling"** in sidebar

**Tests:**

#### View Voice Stats:
1. Check total calls count
2. See active calls
3. Review average duration
4. Check success rate

#### Check Voice Health:
1. View Voice Orchestrator status
2. Should show: "Connected" (green) or "Offline" (red)
3. Port: 8004

#### Configure IVR:
1. Scroll to IVR Configuration
2. Set welcome message
3. Select language
4. Set max call duration
5. Click "Save Settings"

**Note:** To actually test voice calls, you need to integrate with Twilio or similar service.

---

### Test 13: Email Support

**Access:** Click **"Email Support"** in sidebar

**Tests:**

#### View Email Stats:
1. Check emails processed count
2. See pending queue
3. Review avg response time
4. Check success rate

#### Check Email Worker Health:
1. View IMAP connection status
2. View SMTP connection status
3. Should show "Connected" when configured

#### Configure Email:
1. Enter IMAP server (e.g., imap.gmail.com)
2. Enter SMTP server (e.g., smtp.gmail.com)
3. Set email address
4. Configure auto-reply template
5. Set check interval
6. Click "Save Settings"

**Note:** Requires actual email account credentials to work.

---

### Test 14: Integrations

**Access:** Click **"Integrations"** in sidebar

**Tests:**

#### View Integrations:
1. See 8 integration cards:
   - Salesforce CRM
   - Slack
   - Microsoft Teams
   - Google Analytics
   - Stripe
   - Zendesk
   - SendGrid
   - Twilio
2. Check which are "Connected" vs "Not Connected"

#### Connect Integration:
1. Click "Configure" on an integration
2. Enter API credentials
3. Test connection
4. Save

#### Webhooks:
1. Scroll to webhooks section
2. Add webhook URL
3. Select events to trigger
4. Save

#### API Keys:
1. View existing API keys
2. Rotate keys if needed
3. Add new API key

---

### Test 15: Cost Analysis

**Access:** Click **"Cost Analysis"** in sidebar

**Tests:**

#### View Costs:
1. Check total LLM costs
2. Review cost per provider (OpenAI, Anthropic, etc.)
3. See tokens used
4. Check cost trends chart

#### Filter by Date:
1. Select date range
2. View costs for that period
3. Compare different time periods

#### Export Costs:
1. Click "Export Cost Report"
2. Download CSV/JSON
3. Analyze in Excel

---

### Test 16: Settings

**Access:** Click **"Settings"** in sidebar

**Tests:**

#### LLM Providers:
1. Configure OpenAI API key
2. Configure Anthropic API key
3. Set preferred provider
4. Test connection

#### System Settings:
1. Set cache TTL
2. Configure rate limits
3. Set escalation thresholds
4. Save changes

---

### Test 17: System Logs

**Access:** Click **"System Logs"** in sidebar

**Tests:**

#### View Logs:
1. See real-time logs
2. Filter by level (Info, Warning, Error)
3. Filter by service
4. Search logs

#### Export Logs:
1. Select date range
2. Click "Export Logs"
3. Download log file

---

## 🧪 Advanced Testing Scenarios

### Scenario 1: End-to-End RAG Flow

1. **Upload Knowledge:**
   - Go to Knowledge Base
   - Upload a document about your product
   - Wait for indexing

2. **Test Retrieval:**
   - Go to Chat Widget
   - Ask question about document content
   - Should get answer with citations

3. **Check Analytics:**
   - Go to Analytics
   - See the interaction logged
   - Check confidence score

### Scenario 2: Multi-Channel Support

1. **Chat Query:**
   - User asks via chat widget
   - Get response

2. **Email Query:**
   - Send email to configured address
   - Email worker processes it
   - Auto-reply sent

3. **Voice Query:**
   - Call IVR number
   - IVR system responds
   - Call logged

4. **View All:**
   - Check Conversations for chat
   - Check Email for email interaction
   - Check Voice for call log

### Scenario 3: Escalation Flow

1. **Trigger Escalation:**
   - Send angry message in chat
   - System detects negative sentiment

2. **View Escalation:**
   - Go to Sentiment section
   - See escalated conversation
   - Assign to human agent

3. **Resolve:**
   - Mark as resolved
   - Check resolution metrics

---

## 📊 Testing Checklist

Use this checklist to verify all features work:

### Backend Services
- [ ] Gateway API (8000) responding
- [ ] Chat Orchestrator (8002) responding
- [ ] Ingestion Service (8001) responding
- [ ] Voice Orchestrator (8004) responding
- [ ] Email Worker running

### Frontend Access
- [ ] Welcome page (index.html) opens
- [ ] Control Center opens
- [ ] Sidebar navigation works
- [ ] All 14 sections load

### Core Features
- [ ] Chat widget sends/receives messages
- [ ] Multi-language translation works
- [ ] Sentiment analysis detects emotions
- [ ] Cache stores and retrieves responses
- [ ] Rate limiting blocks excessive requests
- [ ] Knowledge base answers questions
- [ ] Conversations are logged

### Channels
- [ ] Voice section shows stats
- [ ] Email section shows stats
- [ ] Integrations section loads

### Admin Functions
- [ ] Analytics dashboard shows data
- [ ] Cost tracking shows LLM usage
- [ ] Settings can be changed
- [ ] Logs display properly
- [ ] Export functions work
- [ ] Refresh button updates data

---

## 🐛 Troubleshooting

### Issue: Backend not starting

**Solution:**
```powershell
# Check if Python is installed
python --version

# Check if dependencies are installed
pip list

# Try starting manually
python run_local.py
```

### Issue: Frontend shows "Offline"

**Solution:**
1. Check backend is running: `.\status.ps1`
2. Check http://localhost:8000/health in browser
3. Refresh frontend page (Ctrl+F5)
4. Check browser console for errors (F12)

### Issue: Sidebar not responding

**Solution:**
1. Hard refresh: Ctrl+F5
2. Clear browser cache
3. Check browser console for JavaScript errors
4. Verify control-center-sections.js and control-center-functions.js loaded

### Issue: No data in sections

**Solution:**
1. Ensure backend is running
2. Check connection status (top-right corner)
3. Click "Refresh" button
4. Open browser console to see API errors
5. Verify API is accessible: http://localhost:8000/docs

---

## 🎯 Quick Test Commands

### PowerShell Commands:
```powershell
# Start platform
.\launch.ps1

# Check status
.\status.ps1

# Run tests
.\test.ps1

# Stop platform
.\stop.ps1
```

### Browser URLs:
```
Welcome Page:        file:///C:/ahmed%20adel/Personal/projects/copilot/index.html
Control Center:      file:///C:/ahmed%20adel/Personal/projects/copilot/clients/admin-console/control-center.html
Chat Widget:         file:///C:/ahmed%20adel/Personal/projects/copilot/clients/web-widget/index.html
API Docs:            http://localhost:8000/docs
Health Check:        http://localhost:8000/health
```

### API Test (PowerShell):
```powershell
# Test chat endpoint
$body = @{
    message = "Hello, how are you?"
    session_id = "test-123"
} | ConvertTo-Json

Invoke-RestMethod -Uri "http://localhost:8000/chat" -Method POST -Body $body -ContentType "application/json"
```

---

## 🎉 Success Criteria

You've successfully tested the platform when:

✅ All backend services are running
✅ Welcome page shows "Services Online"
✅ Control Center sidebar navigation works
✅ Chat widget sends and receives messages
✅ Analytics dashboard shows data and charts
✅ All 14 sections are accessible
✅ Data refreshes when clicking refresh button
✅ Export functions download files
✅ Settings can be changed and saved
✅ Logs display activity

**You're ready to use the Copilot Platform! 🚀**
