# 🎯 Quick Reference Card

## Start Platform

### One-Click Launch ⭐ RECOMMENDED
```powershell
.\launch.ps1
```
or
```bat
launch.bat
```
or **double-click** `launch.bat`

**What opens:** 
- ✅ Backend (auto-starts if not running)
- ✅ Control Center dashboard (ONE page only)
- ✅ Connection status visible

---

## Stop Platform

```powershell
.\stop.ps1
```
or
```bat
stop.bat
```

---

## Check Status

```powershell
.\status.ps1
```

---

## Access Points

### Control Center (Main Dashboard)
```
clients/admin-console/control-center.html
```
**Everything you need in one place!**

### Backend API
```
http://localhost:8000
```

### API Documentation
```
http://localhost:8000/docs
```

### Health Check
```
http://localhost:8000/health
```

---

## Connection Status Colors

🟡 **Yellow - "Connecting..."**
- Backend is starting up
- Please wait...

🟢 **Green - "System Online"**
- Backend is ready
- All features available

🔴 **Red - "Backend Offline"**
- Backend not running
- Run `launch.ps1` or check terminal for errors

---

## Control Center Navigation

### Top Navigation
- **Menu Button** (☰) - Toggle sidebar
- **Connection Status** - See backend status
- **Refresh Button** - Manual refresh (auto-refreshes every 30s)

### Sidebar Sections
1. 📊 Dashboard
2. 📈 Analytics
3. 🌍 Multi-language
4. 😊 Sentiment
5. ⚡ Cache
6. 🛡️ Rate Limiting
7. 🎓 Knowledge Base
8. 💬 Conversations
9. 💰 Costs
10. ⚙️ Settings
11. 📝 Logs

---

## Common Tasks

### Test the Chat
1. Open Control Center
2. Click **"Test Chat"** button in Dashboard
3. Type message & send

### View Analytics
1. Click **"Analytics"** in sidebar
2. See charts, trends, metrics
3. Click **"Export"** to download

### Manage Translations
1. Click **"Multi-language"** in sidebar
2. View language statistics
3. Lookup/cleanup cache

### Clear Cache
1. Click **"Cache"** in sidebar
2. Click **"Clear Cache"** button
3. Confirm

### Block Abusive User
1. Click **"Rate Limiting"** in sidebar
2. Scroll to **"Manual Blocking"** section
3. Enter IP/email/API key
4. Set duration & reason
5. Click **"Block"**

### Review Knowledge Gaps
1. Click **"Knowledge Base"** in sidebar
2. See unanswered questions
3. Review FAQ suggestions
4. Approve helpful ones

### Export Data
- Every section has **"Export"** button
- Click to download JSON
- Use for analysis, backups, reports

---

## Troubleshooting

### Backend Won't Start
```powershell
# Check Python
python --version

# Try manual start
python run_local.py
```

### Port in Use
```powershell
# Stop everything
.\stop.ps1

# Try again
.\launch.ps1
```

### Can't Connect
1. Check connection status (top-right)
2. Visit http://localhost:8000/health
3. Check terminal for errors
4. Restart: `.\restart.ps1`

---

## Keyboard Shortcuts

- **Ctrl+R** - Refresh current section
- **Esc** - Close modal/dialog
- **Tab** - Navigate form fields
- **Enter** - Submit form/action

---

## Files to Know

### Documentation
- `README.md` - Main overview
- `LAUNCH-GUIDE.md` - Launch process details
- `INDEX.md` - Complete file navigation
- `clients/admin-console/CONTROL-CENTER-README.md` - Dashboard docs

### Scripts
- `launch.ps1` / `launch.bat` - Start everything
- `start.ps1` / `start.bat` - Start backend only
- `stop.ps1` / `stop.bat` - Stop everything
- `status.ps1` - Check status
- `restart.ps1` - Restart services

### Configuration
- `config.yaml` - Main config (API keys, settings)
- `services/gateway-api/database.db` - SQLite database

---

## Pro Tips 💡

### 1. Bookmark Control Center
After first launch, bookmark the page for instant access

### 2. Keep Terminal Open
Don't close the terminal where backend is running

### 3. Use Connection Status
Watch the status badge - green means ready!

### 4. Auto-Refresh
Dashboard refreshes every 30s, but you can click Refresh anytime

### 5. Export Regularly
Use Export buttons to backup your analytics & data

### 6. Test Chat Built-in
No need for separate chat page - use the Test Chat button!

### 7. Mobile Works
Control Center is mobile-responsive - access from phone/tablet

### 8. One Command to Rule Them All
Just remember: `.\launch.ps1` does everything!

---

## Quick Stats

**Platform:**
- 8 Core Features
- 11 Dashboard Sections
- 30+ Interactive Charts
- 32+ Admin API Endpoints
- 20+ Languages Supported
- 13 Database Tables

**Files:**
- 30+ Total Files
- 9 Documentation Files
- 3,100+ Lines in Control Center
- 100% Production Ready

---

## Support Resources

**Documentation:**
- LAUNCH-GUIDE.md - Launch troubleshooting
- INDEX.md - File navigation
- CONTROL-CENTER-README.md - Dashboard guide
- QUICK_REFERENCE.md - API reference

**Scripts:**
- test-features.ps1 - Test all features
- demo.ps1 - Interactive demo

---

## Remember! 🎯

**Old Way (Confusing):**
- Multiple pages open
- Not sure which to use
- Localhost not working

**New Way (Simple):**
- One command: `.\launch.ps1`
- One page: Control Center
- Connection status visible
- Everything in one place!

---

**🎉 You're all set! Just run `.\launch.ps1` and start managing your AI platform!**
