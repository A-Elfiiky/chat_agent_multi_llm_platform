# Test the Copilot Platform

Write-Host "===== Copilot Platform Test Suite =====" -ForegroundColor Cyan
Write-Host ""

# Check if services are running
Write-Host "[1/5] Checking if services are running..." -ForegroundColor Yellow
try {
    $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -ErrorAction Stop
    Write-Host "✅ Gateway API is running" -ForegroundColor Green
} catch {
    Write-Host "❌ Services not running. Please start with: python run_local.py" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "[2/5] Testing Chat API..." -ForegroundColor Yellow
$chatBody = @{
    message = "What is your return policy?"
} | ConvertTo-Json

try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" `
        -Method POST `
        -Headers @{
            "Content-Type"="application/json"
            "X-API-Key"="secret-client-key-123"
        } `
        -Body $chatBody

    Write-Host "✅ Chat API Response:" -ForegroundColor Green
    Write-Host "   Answer: $($response.answer_text.Substring(0, [Math]::Min(100, $response.answer_text.Length)))..."
    Write-Host "   Confidence: $($response.confidence)"
    Write-Host "   Citations: $($response.citations.Count)"
} catch {
    Write-Host "❌ Chat API test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[3/5] Testing Search API..." -ForegroundColor Yellow
$searchBody = @{
    query = "shipping"
    k = 3
} | ConvertTo-Json

try {
    $searchResults = Invoke-RestMethod -Uri "http://localhost:8001/search" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $searchBody

    Write-Host "✅ Search API Response:" -ForegroundColor Green
    Write-Host "   Results found: $($searchResults.results.Count)"
    if ($searchResults.results.Count -gt 0) {
        Write-Host "   Top result score: $($searchResults.results[0].score)"
    }
} catch {
    Write-Host "❌ Search API test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[4/5] Testing Admin Stats..." -ForegroundColor Yellow
try {
    $stats = Invoke-RestMethod -Uri "http://localhost:8000/admin/stats" `
        -Headers @{"X-API-Key"="admin-key-456"}

    Write-Host "✅ Admin Stats:" -ForegroundColor Green
    Write-Host "   Total Interactions: $($stats.total_interactions)"
    Write-Host "   Avg Latency: $([Math]::Round($stats.avg_latency_ms, 2)) ms"
    Write-Host "   Providers: $($stats.provider_usage.Keys -join ', ')"
} catch {
    Write-Host "❌ Admin stats test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "[5/5] Testing Voice Webhook..." -ForegroundColor Yellow
try {
    $voiceResponse = Invoke-RestMethod -Uri "http://localhost:8004/voice/webhook" `
        -Method POST `
        -ContentType "application/x-www-form-urlencoded" `
        -Body "CallSid=test123"

    Write-Host "✅ Voice webhook returned TwiML" -ForegroundColor Green
    Write-Host "   Response length: $($voiceResponse.Length) chars"
} catch {
    Write-Host "❌ Voice webhook test failed: $_" -ForegroundColor Red
}

Write-Host ""
Write-Host "===== Test Complete =====" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "  • Open clients/web-widget/index.html in browser"
Write-Host "  • Open clients/admin-console/index.html in browser"
Write-Host "  • View API docs: http://localhost:8000/docs"
