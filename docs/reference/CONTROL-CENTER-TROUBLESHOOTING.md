# Control Center Not Working - Troubleshooting Guide

## Problem: Sections Not Loading

You're seeing the sidebar but when you click on items like Dashboard, Analytics, Voice, etc., the content doesn't load.

## Root Cause Analysis

The Control Center has 3 files that must work together:
1. `control-center.html` - Main HTML with sidebar
2. `control-center-sections.js` - Section templates (SECTIONS object)
3. `control-center-functions.js` - Data loading functions

## Solution Steps

### Step 1: Verify Files Exist

Check that all 3 files are in `clients/admin-console/`:
```powershell
cd 'c:\ahmed adel\Personal\projects\copilot\clients\admin-console'
dir control-center*
```

Expected output:
- control-center.html
- control-center-sections.js
- control-center-functions.js
- platform-config.js

### Step 2: Open with Browser Console

1. Double-click `control-center.html`
2. Press `F12` to open Developer Tools
3. Go to "Console" tab
4. Look for errors

### Step 3: Check Console Logs

You should see:
```
Injecting sections... [analytics, translation, sentiment, cache, ...]
✓ Injected section: analytics
✓ Injected section: translation
...
Section injection complete
```

If you see:
- `SECTIONS object not loaded!` → control-center-sections.js didn't load
- `Section element not found` → HTML structure mismatch
- JavaScript errors → Code syntax issue

### Step 4: Test File Loading

Open Developer Tools → Network tab:
1. Refresh page (Ctrl+F5)
2. Check if these files loaded:
   - control-center-sections.js (Status: 200)
   - control-center-functions.js (Status: 200)
   - platform-config.js (Status: 200)

If Status is 404 → File path wrong
If Status is "blocked" → CORS issue (use file:// protocol)

### Step 5: Manual Test

Create `test-sections.html` in same folder:
```html
<!DOCTYPE html>
<html>
<head><title>Test</title></head>
<body>
    <h1>Section Test</h1>
    <div id="output"></div>
    <script src="control-center-sections.js"></script>
    <script>
        const div = document.getElementById('output');
        if (typeof SECTIONS !== 'undefined') {
            div.innerHTML = '<p style="color:green;">✓ SECTIONS loaded!</p>';
            div.innerHTML += '<p>Sections: ' + Object.keys(SECTIONS).join(', ') + '</p>';
        } else {
            div.innerHTML = '<p style="color:red;">✗ SECTIONS NOT loaded</p>';
        }
    </script>
</body>
</html>
```

Open this file. If it shows "SECTIONS loaded!", the file works.

## Common Issues & Fixes

### Issue 1: "SECTIONS is not defined"

**Cause:** control-center-sections.js not loading

**Fix:**
1. Check file exists
2. Check file path in HTML:
   ```html
   <script src="control-center-sections.js"></script>
   ```
3. Try absolute path:
   ```html
   <script src="./control-center-sections.js"></script>
   ```

### Issue 2: Sections appear empty

**Cause:** injectSectionHTML() not running

**Fix:**
Check console for:
```javascript
document.addEventListener('DOMContentLoaded', function() {
    injectSectionHTML();  // This must run
    initializeCharts();
    loadDashboardData();
});
```

### Issue 3: Clicking sidebar does nothing

**Cause:** JavaScript error preventing navigation

**Fix:**
1. Open console (F12)
2. Click a sidebar item
3. Look for errors like:
   - "showSection is not defined"
   - "event.target.closest is not a function"
   - Any red errors

### Issue 4: Backend not running

**Cause:** APIs returning 404/500

**Fix:**
```powershell
# Start backend
.\launch.ps1

# Or
python run_local.py

# Check health
Invoke-RestMethod http://localhost:8000/health
```

## Quick Diagnostic Script

Run this in PowerShell:

```powershell
Write-Host "Control Center Diagnostic" -ForegroundColor Cyan
Write-Host ""

# Check files exist
$basePath = "c:\ahmed adel\Personal\projects\copilot\clients\admin-console"
$files = @(
    "control-center.html",
    "control-center-sections.js",
    "control-center-functions.js",
    "platform-config.js"
)

foreach ($file in $files) {
    $path = Join-Path $basePath $file
    if (Test-Path $path) {
        $size = (Get-Item $path).Length
        Write-Host "✓ $file ($size bytes)" -ForegroundColor Green
    } else {
        Write-Host "✗ $file MISSING!" -ForegroundColor Red
    }
}

Write-Host ""

# Check backend
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2
    Write-Host "✓ Backend running" -ForegroundColor Green
    Write-Host "  Response: $health" -ForegroundColor Gray
} catch {
    Write-Host "✗ Backend offline" -ForegroundColor Red
    Write-Host "  Run: .\launch.ps1" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Next steps:" -ForegroundColor Cyan
Write-Host "1. Open: $basePath\control-center.html" -ForegroundColor White
Write-Host "2. Press F12 to open console" -ForegroundColor White
Write-Host "3. Check for errors in console" -ForegroundColor White
Write-Host "4. Try clicking sidebar items" -ForegroundColor White
```

## Testing Each Section

### Test Dashboard:
1. Open Control Center
2. Should load automatically (first section)
3. Check for 4 stat cards at top
4. Check for 2 charts (traffic, sentiment)
5. Check "Popular Questions" table

### Test Voice & Calling:
1. Click "Voice & Calling" in sidebar
2. Should see:
   - 4 stats (Total Calls, Active Calls, etc.)
   - Voice Orchestrator Status card
   - Call History table
   - IVR Configuration form
   - Analytics chart

### Test Integrations:
1. Click "Integrations" in sidebar
2. Should see 7 integration cards:
   - Twilio (Connected - green badge)
   - Deepgram (Connected)
   - Groq (Connected)
   - OpenAI (Connected)
   - ElevenLabs (Connected)
   - Supabase (Connected)
   - Ngrok (Connected)
3. Each shows status from platform-config.js

## Integration Testing

The `.env` file values are now loaded in `platform-config.js`:

### Configured Integrations:
- ✅ Twilio: Account SID ACXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
- ✅ Deepgram: Speech-to-text enabled
- ✅ Groq: Fast LLM inference
- ✅ OpenAI: GPT models
- ✅ ElevenLabs: Voice synthesis
- ✅ Supabase: Database at your-supabase-project.supabase.co
- ✅ Ngrok: Tunnel at your-ngrok-or-public-url.example.com

### To Test Integrations:
1. Open Control Center
2. Click "Integrations"
3. All 7 should show "Connected" (green badge)
4. Click any integration card for details

## Expected Behavior

### When Working Properly:
1. **Page Load:**
   - Console shows: "Injecting sections..."
   - Console shows: "✓ Injected section: ..." for each
   - Console shows: "Section injection complete"

2. **Sidebar Click:**
   - Active item highlights
   - Content area changes
   - Page title updates
   - Data loads (may take 1-2 seconds)

3. **Data Display:**
   - Stats show numbers (not 0)
   - Charts render
   - Tables populate
   - No "Loading..." stuck state

### When Not Working:
1. **Page Load:**
   - Console shows errors
   - Sections stay empty
   - No injection logs

2. **Sidebar Click:**
   - Content doesn't change
   - No errors in console
   - Active state doesn't update

3. **Data Display:**
   - All stats show 0
   - Charts don't render
   - Tables show "No data"
   - Connection status: "Offline"

## Emergency Fix

If nothing works, try this minimal version:

1. Open `control-center.html`
2. Press F12 → Console
3. Paste this code:

```javascript
// Force reload sections
if (typeof SECTIONS === 'undefined') {
    console.error('SECTIONS not loaded!');
    alert('Section templates not loaded. Check control-center-sections.js');
} else {
    console.log('SECTIONS loaded:', Object.keys(SECTIONS));
    injectSectionHTML();
    console.log('Sections injected!');
}
```

4. If it works, sections should appear
5. If error, check which file is missing

## Get Help

If still not working:

1. **Check console logs** - Screenshot any errors
2. **Check Network tab** - See which files failed to load
3. **Verify file paths** - All files in same folder?
4. **Try different browser** - Chrome, Firefox, Edge
5. **Clear cache** - Hard refresh (Ctrl+F5)

## Success Checklist

- [ ] All 4 files exist in clients/admin-console/
- [ ] control-center.html opens in browser
- [ ] F12 console shows no errors
- [ ] Console shows "Section injection complete"
- [ ] Sidebar items are clickable
- [ ] Content changes when clicking sidebar
- [ ] Backend is running (green status badge)
- [ ] Integrations show "Connected"
- [ ] Charts render properly
- [ ] Data loads (not all zeros)

If all checked ✓, Control Center is working! 🎉
