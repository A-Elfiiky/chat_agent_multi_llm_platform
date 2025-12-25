# Control Center Guide

## 📍 What is the Control Center?

The **Control Center** is the comprehensive admin dashboard for the Copilot Platform. It features:

- **Sidebar Navigation** - Easy access to all 14 platform sections
- **Real-time Monitoring** - Live stats and health checks
- **Full Feature Management** - Analytics, Translation, Sentiment, Cache, Rate Limiting, Knowledge Base, Conversations, Voice, Email, Integrations, Costs, Settings, and Logs

## 🚀 How to Access

### Method 1: Via Welcome Page (Recommended)
1. Open `index.html` in your browser
2. Click "Open Control Center" card
3. The Control Center will open with full sidebar navigation

### Method 2: Direct Access
1. Navigate to `clients/admin-console/control-center.html`
2. Double-click to open in your default browser
3. Sidebar should appear on the left

## 🗂️ Sidebar Sections

The sidebar is organized into 4 categories:

### Overview
- **Dashboard** 📊 - Real-time platform overview with charts
- **Analytics** 📈 - Comprehensive metrics and insights

### Features
- **Multi-language** 🌍 - Translation and language management
- **Sentiment & Escalation** 😊 - Customer emotion tracking
- **Response Caching** ⚡ - Cache management and optimization
- **Rate Limiting** 🛡️ - API protection and abuse prevention
- **Knowledge Base** 🎓 - Auto-learning and FAQ management
- **Conversations** 💬 - Chat history and session management

### Channels
- **Voice & Calling** 📞 - IVR system and call management
- **Email Support** 📧 - Email automation and responses
- **Integrations** 🔗 - CRM, Slack, Teams and external systems

### Management
- **Cost Analysis** 💰 - LLM usage and cost tracking
- **Settings** ⚙️ - Platform configuration
- **System Logs** 📝 - Activity and error logs

## 🔧 Troubleshooting Sidebar Navigation

### Issue: Sidebar not showing
**Solution:**
1. Check browser console for JavaScript errors (F12)
2. Ensure `control-center-sections.js` and `control-center-functions.js` are in the same folder
3. Refresh the page (Ctrl+F5 for hard refresh)

### Issue: Clicking sidebar items doesn't work
**Solution:**
1. Open browser console (F12) and check for errors
2. Verify backend is running: http://localhost:8000/health
3. Check if scripts loaded properly in Network tab
4. Try clearing browser cache

### Issue: Sections appear empty
**Solution:**
1. Verify backend services are running (`.\status.ps1`)
2. Check connection status in top-right corner
3. Click the Refresh button to reload data
4. Check browser console for API errors

### Issue: Mobile sidebar collapsed
**Solution:**
- On mobile/narrow screens, sidebar auto-collapses
- Click the hamburger menu (☰) button to toggle sidebar
- This is normal responsive behavior

## 📡 Backend Requirements

The Control Center requires these backend services:

| Service | Port | Purpose |
|---------|------|---------|
| Gateway API | 8000 | Main API and data |
| Chat Orchestrator | 8002 | Chat functionality |
| Ingestion Service | 8001 | Knowledge base |
| Voice Orchestrator | 8004 | Voice features |
| Email Worker | Background | Email processing |

**Start all services:**
```powershell
.\launch.ps1
```

## 🌐 Frontend Architecture

**Important:** The Control Center is a **static HTML application**:

- ✅ No port needed (opens with `file://` protocol)
- ✅ Can open directly in browser
- ✅ Connects to backend APIs on localhost:8000-8004
- ✅ Works offline for UI navigation (data requires backend)

## 🎯 Key Features

### Auto-Connect
- Control Center automatically checks backend health every 5 seconds
- Connection status shown in top-right corner
- Will reconnect when services come online

### Data Refresh
- Dashboard auto-refreshes every 30 seconds
- Manual refresh button available in header
- Each section loads data on first view

### Responsive Design
- Desktop: Full sidebar visible
- Tablet: Sidebar toggleable
- Mobile: Sidebar collapsed by default

## 📂 File Structure

```
clients/admin-console/
├── control-center.html           # Main dashboard (1,494 lines)
├── control-center-sections.js    # HTML templates for all sections
├── control-center-functions.js   # API integration and business logic
├── index.html                    # Legacy admin console
└── CONTROL-CENTER-README.md      # Detailed documentation
```

## 💡 Tips

1. **Use Control Center as primary interface** - It includes all features in one place
2. **Check connection status** - Top-right badge shows backend health
3. **Navigate with sidebar** - All 14 sections accessible from sidebar
4. **Export data** - Each section has export functionality
5. **Test chat** - Use "Test Chat" button to verify chatbot works

## 🆘 Still Having Issues?

### Check These:
1. ✅ Backend running? → `.\status.ps1`
2. ✅ JavaScript enabled in browser?
3. ✅ Browser console shows errors? (F12)
4. ✅ Files in correct location?
5. ✅ Network tab shows 404 errors?

### Common Fixes:
- **Hard refresh:** Ctrl+F5 (Windows) or Cmd+Shift+R (Mac)
- **Clear cache:** Settings → Clear browsing data
- **Try different browser:** Chrome, Firefox, Edge
- **Check file paths:** Ensure all files are in `clients/admin-console/`

## 📞 Port Information

**Question: "Which port for the frontend page?"**

**Answer:** Frontend pages are **static HTML files** - they don't use a port!

- Frontend files open with `file://` protocol (local file system)
- Only backend APIs use ports (8000-8004)
- You open HTML files directly in your browser (double-click)
- No web server needed for frontend

**Backend Ports:**
- Gateway API: `http://localhost:8000`
- Chat Orchestrator: `http://localhost:8002`
- Ingestion: `http://localhost:8001`
- Voice: `http://localhost:8004`

## 🎉 Success Checklist

- [ ] Backend services running
- [ ] `index.html` opens and shows "Services Online"
- [ ] Control Center opens when clicking the card
- [ ] Sidebar visible on left side
- [ ] Clicking sidebar items changes content
- [ ] Connection status shows "System Online"
- [ ] Dashboard shows data and charts

If all checked, you're ready to go! 🚀
