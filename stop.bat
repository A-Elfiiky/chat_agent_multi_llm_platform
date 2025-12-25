@echo off
REM Copilot Platform Stop Script (Windows Batch)
REM This script stops all running microservices

echo.
echo =====================================
echo   Copilot Platform - Stopping...
echo =====================================
echo.

echo Stopping all Python processes...
echo.

taskkill /F /IM python.exe /T >nul 2>&1

if %ERRORLEVEL% EQU 0 (
    echo Services stopped successfully!
) else (
    echo No running services found.
)

echo.
echo To start again, run: start.bat
echo.
pause
