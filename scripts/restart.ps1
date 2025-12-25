#!/usr/bin/env pwsh
# Copilot Platform Restart Script
# This script stops and then starts all microservices

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Copilot Platform - Restarting..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

# Stop services
Write-Host "🛑 Stopping existing services..." -ForegroundColor Yellow
& "$PSScriptRoot\stop.ps1"

# Wait a moment
Write-Host "⏳ Waiting for cleanup..." -ForegroundColor Yellow
Start-Sleep -Seconds 3

# Start services
Write-Host ""
Write-Host "🚀 Starting services..." -ForegroundColor Green
& "$PSScriptRoot\start.ps1"
