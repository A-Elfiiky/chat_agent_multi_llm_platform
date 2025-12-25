#!/usr/bin/env pwsh
# Simple HTTP Server for Testing Frontend
# This starts a simple web server to serve the HTML files

Write-Host ""
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host "  Starting Frontend Server..." -ForegroundColor Cyan
Write-Host "=====================================" -ForegroundColor Cyan
Write-Host ""

$port = 3000

Write-Host "Starting HTTP server on port $port..." -ForegroundColor Yellow
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor Cyan
Write-Host "  • Landing Page:  " -NoNewline; Write-Host "http://localhost:$port" -ForegroundColor Green
Write-Host "  • Chat Widget:   " -NoNewline; Write-Host "http://localhost:$port/clients/web-widget/" -ForegroundColor Green
Write-Host "  • Admin Console: " -NoNewline; Write-Host "http://localhost:$port/clients/admin-console/" -ForegroundColor Green
Write-Host ""
Write-Host "Press Ctrl+C to stop the server" -ForegroundColor Yellow
Write-Host ""

# Start Python's built-in HTTP server
python -m http.server $port
