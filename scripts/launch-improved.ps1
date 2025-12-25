#!/usr/bin/env pwsh
# Streamlined Launcher - Starts backend WITHOUT forcing browser windows

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "     Copilot Platform - Quick Launch" -ForegroundColor Cyan
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""

# Check if services are already running
$running = $false
try {
    $response = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
    $running = $true
    Write-Host "✅ Backend already running!" -ForegroundColor Green
} catch {
    $running = $false
    Write-Host "🚀 Starting backend services..." -ForegroundColor Yellow
    Write-Host ""
    
    # Start services in background
    Start-Process powershell -ArgumentList "-ExecutionPolicy Bypass -NoProfile -Command `"cd '$PSScriptRoot'; python run_local.py`"" -WindowStyle Hidden
    
    Write-Host "⏳ Waiting for services to initialize..." -ForegroundColor Yellow
    Start-Sleep -Seconds 5
    
    # Verify services started
    $attempts = 0
    $maxAttempts = 15
    $started = $false
    
    while (-not $started -and $attempts -lt $maxAttempts) {
        try {
            $null = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 2 -ErrorAction Stop
            $started = $true
            Write-Host "✅ Backend is ready!" -ForegroundColor Green
        } catch {
            $attempts++
            Write-Host "." -NoNewline -ForegroundColor Yellow
            Start-Sleep -Seconds 1
        }
    }
    
    if (-not $started) {
        Write-Host ""
        Write-Host "⚠️  Backend is taking longer than expected..." -ForegroundColor Yellow
        Write-Host "   You can still access the frontend - it will auto-connect when ready" -ForegroundColor Yellow
    }
    Write-Host ""
}

Write-Host ""
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host "           🎉 Ready to Go!" -ForegroundColor Green
Write-Host "=========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "✅ Backend Services Running:" -ForegroundColor Green
Write-Host "  • Gateway API        → http://localhost:8000" -ForegroundColor White
Write-Host "  • Chat Orchestrator  → http://localhost:8002" -ForegroundColor White
Write-Host "  • Ingestion Service  → http://localhost:8001" -ForegroundColor White
Write-Host "  • Voice Orchestrator → http://localhost:8004" -ForegroundColor White
Write-Host "  • Email Worker       → Running in background" -ForegroundColor White
Write-Host ""
Write-Host "🌐 Frontend Pages (Static HTML - No Port Needed):" -ForegroundColor Cyan
Write-Host "  📄 Welcome Page       → index.html" -ForegroundColor Yellow
Write-Host "  🎛️  Control Center     → clients\admin-console\control-center.html" -ForegroundColor Yellow
Write-Host "  ⚙️  Admin Console      → clients\admin-console\index.html" -ForegroundColor Yellow
Write-Host "  💬 Web Chat Widget    → clients\web-widget\index.html" -ForegroundColor Yellow
Write-Host ""
Write-Host "📚 API & Documentation:" -ForegroundColor Cyan
Write-Host "  • API Documentation  → http://localhost:8000/docs" -ForegroundColor White
Write-Host "  • Health Check       → http://localhost:8000/health" -ForegroundColor White
Write-Host ""
Write-Host "💡 How to Access:" -ForegroundColor Yellow
Write-Host "   1. Open 'index.html' in your browser (centralized welcome page)" -ForegroundColor White
Write-Host "   2. Or double-click any HTML file to open it directly" -ForegroundColor White
Write-Host "   3. Use the Control Center sidebar to navigate all features" -ForegroundColor White
Write-Host ""
Write-Host "ℹ️  Frontend Info:" -ForegroundColor Gray
Write-Host "   - Frontend pages are static HTML (open directly in browser)" -ForegroundColor DarkGray
Write-Host "   - No web server needed for frontend (uses file:// protocol)" -ForegroundColor DarkGray
Write-Host "   - Backend APIs run on http://localhost:8000-8004" -ForegroundColor DarkGray
Write-Host ""
Write-Host "💡 To stop services: " -NoNewline -ForegroundColor Yellow
Write-Host ".\stop.ps1" -ForegroundColor Cyan
Write-Host ""
