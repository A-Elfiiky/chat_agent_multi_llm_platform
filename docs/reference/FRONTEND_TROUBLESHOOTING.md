# Frontend Troubleshooting Guide

## Issue: Web Pages Not Working

### Common Problems and Solutions

#### 1. "Cannot connect to server" Error

**Symptoms:**
- Chat widget shows "Offline - Service Unavailable"
- Browser console shows CORS or fetch errors
- Admin console displays connection error

**Solutions:**

**A. Ensure Backend Services are Running**
```powershell
# Check status
.\status.ps1

# If services are stopped, start them
.\start.ps1

# Wait 8-10 seconds for initialization
```

**B. Verify Services are Accessible**
Open in browser: http://localhost:8000/health

Should see: `{"status":"healthy"}`

If not working:
- Check if another application is using ports 8000-8004
- Run `netstat -ano | findstr "8000"` to see port usage
- Stop conflicting processes or change ports in `config.yaml`

#### 2. CORS Errors in Browser Console

**Symptoms:**
```
Access to fetch at 'http://localhost:8000/api/v1/chat' from origin 'null' has been blocked by CORS policy
```

**Solutions:**

**A. Use the HTTP Server (Recommended)**
```powershell
# In a separate terminal, start the frontend server
.\serve.ps1

# Then access via http://localhost:3000
```

**B. Or Open with Browser Direct File Protocol**
The HTML files should work with `file://` protocol, but some browsers restrict this.

**C. Use Firefox or Disable CORS (Chrome)**
```bash
# Chrome with CORS disabled (development only!)
chrome.exe --disable-web-security --user-data-dir="C:\temp\chrome-dev"
```

#### 3. Page Loads But No Data Appears

**Symptoms:**
- Admin console shows "-" for all stats
- Chat sends messages but no response
- Browser console shows 404 or 500 errors

**Solutions:**

**A. Check Backend Logs**
Look at the terminal where `run_local.py` is running for errors.

**B. Test Endpoints Manually**
```powershell
# Test health
Invoke-RestMethod -Uri "http://localhost:8000/health"

# Test chat (replace with your message)
$body = @{ message = "test" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" `
    -Method POST `
    -Headers @{"Content-Type"="application/json"; "X-API-Key"="secret-client-key-123"} `
    -Body $body
```

**C. Restart Services**
```powershell
.\restart.ps1
```

#### 4. SSL/Certificate Errors

**Symptoms:**
- HuggingFace model download fails
- Services crash on startup with SSL errors

**Solution:**
This is already handled in `ingestor.py` with SSL verification disabled for development.

If issues persist:
```powershell
# Set environment variables before starting
$env:CURL_CA_BUNDLE = ''
$env:REQUESTS_CA_BUNDLE = ''
python run_local.py
```

#### 5. File Not Found (404) for HTML Files

**Symptoms:**
- Clicking links gives 404
- `clients/web-widget/index.html` not found

**Solutions:**

**A. Check File Paths**
Ensure you're in the project root directory:
```powershell
cd "c:\ahmed adel\Personal\projects\copilot"
```

**B. Use HTTP Server**
```powershell
.\serve.ps1
# Then navigate to http://localhost:3000
```

#### 6. JavaScript Errors in Console

**Symptoms:**
```
TypeError: Cannot read property 'textContent' of null
ReferenceError: sendMessage is not defined
```

**Solutions:**

**A. Hard Refresh Browser**
- Press `Ctrl+Shift+R` (Windows/Linux)
- Or `Cmd+Shift+R` (Mac)

**B. Clear Browser Cache**
- Open DevTools (F12)
- Right-click refresh button → "Empty Cache and Hard Reload"

**C. Check Browser Compatibility**
Use modern browsers: Chrome 90+, Firefox 88+, Edge 90+

## Recommended Workflow

### Method 1: Direct File Access (Simple)

1. Start backend services:
   ```powershell
   .\start.ps1
   ```

2. Open `index.html` in browser:
   - Double-click `index.html` in file explorer
   - Or drag file into browser window

3. Click "Open Chat" or "Open Admin" buttons

### Method 2: HTTP Server (Best for Development)

1. Start backend services (Terminal 1):
   ```powershell
   .\start.ps1
   ```

2. Start frontend server (Terminal 2):
   ```powershell
   .\serve.ps1
   ```

3. Open browser to:
   - http://localhost:3000 (Landing page)
   - http://localhost:3000/clients/web-widget/ (Chat)
   - http://localhost:3000/clients/admin-console/ (Admin)

### Method 3: API Only (No Frontend)

Use the Swagger UI:
1. Start services: `.\start.ps1`
2. Open: http://localhost:8000/docs
3. Test endpoints directly in browser

## Browser Developer Tools

### How to Check for Errors

1. Open DevTools: Press `F12`
2. Click "Console" tab
3. Look for red error messages
4. Click "Network" tab to see failed requests

### Common Console Messages

**✅ Good (Normal):**
```
✅ Gateway API is reachable
Testing connection to Gateway API...
```

**❌ Bad (Problem):**
```
Failed to fetch
TypeError: Cannot read property...
CORS policy: No 'Access-Control-Allow-Origin'
```

## Testing Checklist

Run through this checklist:

- [ ] Backend services are running (`.\status.ps1`)
- [ ] Can access http://localhost:8000/health
- [ ] Can access http://localhost:8000/docs
- [ ] No CORS errors in browser console
- [ ] HTML files exist in correct locations
- [ ] Using modern browser (Chrome/Firefox/Edge)
- [ ] Tried hard refresh (Ctrl+Shift+R)

## Still Having Issues?

### Collect Debug Information

1. **Check service status:**
   ```powershell
   .\status.ps1
   ```

2. **Check browser console:**
   - Press F12
   - Copy any errors from Console tab

3. **Check backend logs:**
   - Look at terminal where `run_local.py` is running
   - Copy any error messages

4. **Test API manually:**
   ```powershell
   .\test.ps1
   ```

### Reset Everything

If all else fails, complete reset:

```powershell
# 1. Stop all services
.\stop.ps1

# 2. Kill any remaining Python processes
taskkill /F /IM python.exe

# 3. Wait a moment
Start-Sleep -Seconds 3

# 4. Start fresh
.\start.ps1

# 5. Hard refresh browser
# Press Ctrl+Shift+R
```

## Port Reference

| Service | Port | Test URL |
|---------|------|----------|
| Gateway API | 8000 | http://localhost:8000/health |
| Ingestion Service | 8001 | http://localhost:8001/health |
| Chat Orchestrator | 8002 | http://localhost:8002/health |
| Voice Orchestrator | 8004 | http://localhost:8004/health |
| Frontend Server (optional) | 3000 | http://localhost:3000 |

## Quick Fixes Summary

| Problem | Quick Fix |
|---------|-----------|
| Services offline | `.\start.ps1` |
| CORS errors | Use `.\serve.ps1` or open index.html |
| Page won't load | Hard refresh (Ctrl+Shift+R) |
| No response from chat | Check `.\status.ps1` and restart |
| 404 errors | Verify you're in project root directory |
| Stale data | `.\restart.ps1` |

---

**For more help, see:**
- `GETTING_STARTED.md` - Initial setup
- `SCRIPTS_GUIDE.md` - Script usage
- `MANUAL_TESTS.md` - API testing
