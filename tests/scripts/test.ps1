#!/usr/bin/env pwsh
# Quick Test Script - Test all platform endpoints

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Copilot Platform - Quick Test" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$passed = 0
$failed = 0

# Test 1: Health Check
Write-Host "[Test 1/5] Health Check..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5 -ErrorAction Stop
    Write-Host "  ✅ Gateway is healthy" -ForegroundColor Green
    $passed++
} catch {
    Write-Host "  ❌ Gateway health check failed" -ForegroundColor Red
    $failed++
}

Write-Host ""

# Test 2: Chat API
Write-Host "[Test 2/5] Chat API..." -ForegroundColor Yellow
try {
    $body = @{ message = "What is your return policy?" } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8000/api/v1/chat" `
        -Method POST `
        -Headers @{
            "Content-Type"="application/json"
            "X-API-Key"="secret-client-key-123"
        } `
        -Body $body `
        -TimeoutSec 10 `
        -ErrorAction Stop
    
    Write-Host "  ✅ Chat API working" -ForegroundColor Green
    Write-Host "     Answer: $($response.answer_text.Substring(0, [Math]::Min(60, $response.answer_text.Length)))..." -ForegroundColor Gray
    Write-Host "     Confidence: $($response.confidence)" -ForegroundColor Gray
    $passed++
} catch {
    Write-Host "  ❌ Chat API failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""

# Test 3: Search API
Write-Host "[Test 3/5] Search API..." -ForegroundColor Yellow
try {
    $body = @{ query = "shipping"; k = 3 } | ConvertTo-Json
    $response = Invoke-RestMethod -Uri "http://localhost:8001/search" `
        -Method POST `
        -Headers @{"Content-Type"="application/json"} `
        -Body $body `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "  ✅ Search API working" -ForegroundColor Green
    Write-Host "     Results found: $($response.results.Count)" -ForegroundColor Gray
    $passed++
} catch {
    Write-Host "  ❌ Search API failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""

# Test 4: Admin Stats
Write-Host "[Test 4/5] Admin Stats..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/admin/stats" `
        -Headers @{"X-API-Key"="admin-key-456"} `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "  ✅ Admin API working" -ForegroundColor Green
    Write-Host "     Total interactions: $($response.total_interactions)" -ForegroundColor Gray
    Write-Host "     Avg latency: $([Math]::Round($response.avg_latency_ms, 2)) ms" -ForegroundColor Gray
    $passed++
} catch {
    Write-Host "  ❌ Admin stats failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

Write-Host ""

# Test 5: Voice Webhook
Write-Host "[Test 5/5] Voice Webhook..." -ForegroundColor Yellow
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8004/voice/webhook" `
        -Method POST `
        -ContentType "application/x-www-form-urlencoded" `
        -Body "CallSid=test123" `
        -TimeoutSec 5 `
        -ErrorAction Stop
    
    Write-Host "  ✅ Voice webhook working" -ForegroundColor Green
    Write-Host "     TwiML response: $($response.Length) chars" -ForegroundColor Gray
    $passed++
} catch {
    Write-Host "  ❌ Voice webhook failed: $($_.Exception.Message)" -ForegroundColor Red
    $failed++
}

# Summary
Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Test Results" -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Passed: " -NoNewline
Write-Host "$passed/5" -ForegroundColor Green
Write-Host "Failed: " -NoNewline
Write-Host "$failed/5" -ForegroundColor $(if ($failed -eq 0) { "Green" } else { "Red" })
Write-Host ""

if ($failed -eq 0) {
    Write-Host "🎉 All tests passed! Platform is fully operational." -ForegroundColor Green
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  • Open clients/web-widget/index.html" -ForegroundColor White
    Write-Host "  • Open clients/admin-console/index.html" -ForegroundColor White
    Write-Host "  • Visit http://localhost:8000/docs" -ForegroundColor White
} else {
    Write-Host "⚠️  Some tests failed. Check service logs." -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Troubleshooting:" -ForegroundColor Cyan
    Write-Host "  • Run: .\status.ps1" -ForegroundColor White
    Write-Host "  • Try: .\restart.ps1" -ForegroundColor White
    Write-Host "  • Check: Terminal output for errors" -ForegroundColor White
}

Write-Host ""
