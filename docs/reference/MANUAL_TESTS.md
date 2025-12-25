# Manual Test Commands

## Prerequisites
Ensure services are running with: `python run_local.py`

## Test 1: Health Check
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/health"
```

## Test 2: Chat API
```powershell
$body = @{ message = "What is your return policy?" } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" -Method POST -Headers @{"Content-Type"="application/json"; "X-API-Key"="secret-client-key-123"} -Body $body
```

## Test 3: Search API
```powershell
$body = @{ query = "shipping"; k = 3 } | ConvertTo-Json
Invoke-RestMethod -Uri "http://localhost:8001/search" -Method POST -Headers @{"Content-Type"="application/json"} -Body $body
```

## Test 4: Admin Stats
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/admin/stats" -Headers @{"X-API-Key"="admin-key-456"}
```

## Test 5: Voice Webhook
```powershell
Invoke-RestMethod -Uri "http://localhost:8004/voice/webhook" -Method POST -ContentType "application/x-www-form-urlencoded" -Body "CallSid=test123"
```

## Browser Tests
- Web Widget: Open `clients/web-widget/index.html`
- Admin Console: Open `clients/admin-console/index.html`
- API Docs: http://localhost:8000/docs
