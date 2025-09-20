@echo off
REM MT5 Bridge Installation Script for Windows
REM Automatically setup MT5 Bridge environment

echo ================================
echo 🚀 MT5 BRIDGE INSTALLATION
echo ================================
echo.

REM Check Python installation
echo 🔍 Checking Python installation...
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Python not found! Please install Python 3.8+ first
    echo 📥 Download from: https://www.python.org/downloads/
    pause
    exit /b 1
)

echo ✅ Python found

REM Check pip
echo 🔍 Checking pip...
pip --version > nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ pip not found! Installing pip...
    python -m ensurepip --upgrade
)

echo ✅ pip ready

REM Create virtual environment (optional but recommended)
echo 🔧 Creating virtual environment...
if not exist "venv" (
    python -m venv venv
    echo ✅ Virtual environment created
) else (
    echo ⚠️  Virtual environment already exists
)

REM Activate virtual environment
echo 🔋 Activating virtual environment...
call venv\Scripts\activate

REM Install requirements
echo 📦 Installing Python dependencies...
pip install -r requirements.txt

if %errorlevel% neq 0 (
    echo ❌ Failed to install dependencies
    pause
    exit /b 1
)

echo ✅ Dependencies installed successfully

REM Create .env file if not exists
echo ⚙️  Setting up configuration...
if not exist ".env" (
    if exist ".env.example" (
        copy ".env.example" ".env"
        echo ✅ Configuration file created: .env
        echo ⚠️  IMPORTANT: Please edit .env file with your MT5 credentials
    ) else (
        echo ❌ .env.example not found
    )
) else (
    echo ⚠️  Configuration file already exists: .env
)

REM Check MT5 installation
echo 🔍 Checking MT5 installation...
set "MT5_PATH=C:\Program Files\MetaTrader 5\terminal64.exe"
if exist "%MT5_PATH%" (
    echo ✅ MT5 found at: %MT5_PATH%
) else (
    echo ⚠️  MT5 not found at default location
    echo    Please check MT5_PATH in .env file
)

echo.
echo ================================
echo ✅ INSTALLATION COMPLETE!
echo ================================
echo.
echo 📋 NEXT STEPS:
echo 1. Edit .env file with your MT5 credentials
echo 2. Make sure MT5 terminal is running
echo 3. Start Docker backend services
echo 4. Run: python run_bridge.py
echo.
echo 📝 Configuration file: .env
echo 📖 Documentation: README.md
echo 🚀 Start command: python run_bridge.py
echo.
echo 🔧 Quick MT5 Setup:
echo - Enable "Auto Trading" in MT5
echo - Allow "Expert Advisors" 
echo - Ensure stable broker connection
echo.

pause