@echo off
echo ===========================================
echo Stopping All MT5 Bridge Processes
echo ===========================================

echo Stopping Python processes running MT5 Bridge...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *bridge*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq *hybrid*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq *mt5*" 2>nul

echo Stopping any Python processes with bridge-related command line...
for /f "tokens=2" %%i in ('tasklist /fi "imagename eq python.exe" /fo csv ^| find "python.exe"') do (
    wmic process where "processid=%%i" get commandline /format:list | find "bridge" >nul
    if not errorlevel 1 (
        echo Stopping process %%i
        taskkill /f /pid %%i 2>nul
    )
)

echo Waiting for processes to stop...
timeout /t 3 /nobreak >nul

echo ===========================================
echo All MT5 Bridge processes stopped
echo You can now safely run cleanup_logs.bat
echo ===========================================

pause