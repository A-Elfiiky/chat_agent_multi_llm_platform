@echo off
REM Copilot Platform Startup Script (Windows Batch)
REM This script starts all microservices

echo.
echo =====================================
echo   Copilot Platform - Starting...
echo =====================================
echo.

echo Starting all services...
echo.

start /B python run_local.py

echo Waiting for services to initialize...
timeout /t 8 /nobreak >nul

echo.
echo Platform is starting!
echo.
echo Services:
echo   - Gateway API        : http://localhost:8000
echo   - Chat Orchestrator  : http://localhost:8002
echo   - Ingestion Service  : http://localhost:8001
echo   - Voice Orchestrator : http://localhost:8004
echo   - Email Worker       : Running in background
echo.
echo Quick Access:
echo   - API Documentation  : http://localhost:8000/docs
echo   - Web Chat Widget    : clients\web-widget\index.html
echo   - Admin Console      : clients\admin-console\index.html
echo.
echo To stop the platform, run: stop.bat
echo.
pause
