@echo off
:restart
echo 🚀 Starting MT5 Client...
python run.py
echo.
echo 🔄 Client stopped. Press any key to restart, or Ctrl+C to exit.
pause >nul
goto restart