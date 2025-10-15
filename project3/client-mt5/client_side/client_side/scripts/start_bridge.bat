@echo off
REM MT5 Bridge Startup Script
REM Quick launcher for MT5 Bridge

title MT5 Bridge - AI Trading Connector

echo ================================
echo 🚀 MT5 BRIDGE STARTUP
echo ================================
echo.

REM Check if virtual environment exists
if exist "venv\Scripts\activate.bat" (
    echo 🔋 Activating virtual environment...
    call venv\Scripts\activate
) else (
    echo ⚠️  Virtual environment not found, using system Python
)

REM Check if .env exists
if not exist ".env" (
    echo ❌ Configuration file (.env) not found!
    echo Please run install.bat first or create .env manually
    pause
    exit /b 1
)

REM Check if MT5 is running
echo 🔍 Checking MT5 terminal...
tasklist /FI "IMAGENAME eq terminal64.exe" 2>NUL | find /I /N "terminal64.exe" > NUL
if "%ERRORLEVEL%"=="0" (
    echo ✅ MT5 terminal detected
) else (
    echo ⚠️  MT5 terminal not detected
    echo.
    echo 🚀 Don't worry! MT5 Bridge will automatically start MT5 terminal
    echo    when you run the bridge application.
    echo.
    echo 📋 Make sure:
    echo    1. MT5 installation path is correct in .env file
    echo    2. Your account credentials are configured
    echo    3. You have internet connection
    echo.
    set /p "continue=Continue with auto-start? (Y/n): "
    if /i "%continue%"=="n" (
        echo Startup cancelled
        pause
        exit /b 1
    )
)

REM Check Docker backend
echo 🔍 Checking Docker backend...
curl -s http://localhost:8000/health > nul 2>&1
if %errorlevel% equ 0 (
    echo ✅ Docker backend is running
) else (
    echo ⚠️  Docker backend not accessible
    echo Please start Docker services first
    echo.
    set /p "continue=Continue anyway? (y/N): "
    if /i not "%continue%"=="y" (
        echo Startup cancelled
        pause
        exit /b 1
    )
)

echo.
echo ================================
echo 🌉 STARTING MT5 BRIDGE
echo ================================
echo.
echo 📊 Monitoring Dashboard: http://localhost:3000/dashboard/
echo 🔗 Backend API: http://localhost:8000
echo 📝 Logs: mt5_bridge.log
echo.
echo Press Ctrl+C to stop gracefully
echo ================================
echo.

REM Start Hybrid MT5 Bridge (WebSocket + Redpanda)
echo Choose MT5 Bridge mode:
echo 1. Hybrid Bridge (WebSocket + Redpanda) - Recommended
echo 2. Standard Bridge (WebSocket only)
echo.
set /p "mode=Enter choice (1 or 2): "

if "%mode%"=="1" (
    echo.
    echo 🌉 Starting Hybrid MT5 Bridge...
    python hybrid_bridge.py
) else if "%mode%"=="2" (
    echo.
    echo 🔗 Starting Standard MT5 Bridge...
    python run_bridge.py
) else (
    echo.
    echo 🌉 Starting Hybrid MT5 Bridge (default)...
    python hybrid_bridge.py
)

echo.
echo ================================
echo 👋 MT5 BRIDGE STOPPED
echo ================================

pause