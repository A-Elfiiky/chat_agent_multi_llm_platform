@echo off
REM Simple Launcher - Starts backend and opens Control Center only

echo.
echo =========================================
echo      Copilot Platform - Quick Launch
echo =========================================
echo.

REM Check if backend is running
curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend already running!
    goto OPEN_BROWSER
)

echo [*] Starting backend services...
echo.

REM Start backend in background
start /B pythonw run_local.py 2>nul
if errorlevel 1 (
    echo [!] pythonw not found, trying python...
    start /MIN python run_local.py
)

echo [*] Waiting for backend to start...
timeout /t 5 /nobreak >nul

REM Wait for backend to be ready
set "MAX_ATTEMPTS=15"
set "ATTEMPTS=0"

:CHECK_BACKEND
if %ATTEMPTS% geq %MAX_ATTEMPTS% (
    echo [!] Backend taking longer than expected...
    echo [!] Opening Control Center anyway - it will auto-connect
    goto OPEN_BROWSER
)

curl -s http://localhost:8000/health >nul 2>&1
if %errorlevel% equ 0 (
    echo [OK] Backend is ready!
    goto OPEN_BROWSER
)

set /a ATTEMPTS+=1
echo .
timeout /t 1 /nobreak >nul
goto CHECK_BACKEND

:OPEN_BROWSER
echo.
echo [*] Opening Control Center...
echo.

start "" "clients\admin-console\control-center.html"

echo.
echo =========================================
echo            Ready to Go!
echo =========================================
echo.
echo What's Running:
echo   - Backend API       : http://localhost:8000
echo   - Control Center    : Opened in browser
echo.
echo Quick Access:
echo   - API Docs          : http://localhost:8000/docs
echo   - Health Check      : http://localhost:8000/health
echo.
echo Control Center Features:
echo   - Test chat interface (click 'Test Chat')
echo   - View all analytics and metrics
echo   - Manage all 8 platform features
echo   - Export data from any section
echo.
echo To stop everything: stop.bat or stop.ps1
echo.
pause
