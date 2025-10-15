@echo off
echo ===========================================
echo Force Cleanup Locked Log Files
echo ===========================================

echo Stopping any running MT5 Bridge processes...
taskkill /f /im python.exe /fi "WINDOWTITLE eq *hybrid_bridge*" 2>nul
taskkill /f /im python.exe /fi "WINDOWTITLE eq *bridge*" 2>nul
timeout /t 2 /nobreak >nul

echo Attempting to force delete locked files...

if exist "mt5_bridge_windows.log" (
    echo Trying to delete mt5_bridge_windows.log...
    del /f /q "mt5_bridge_windows.log" 2>nul
    if exist "mt5_bridge_windows.log" (
        echo File is locked, trying alternative method...
        powershell -Command "Remove-Item -Path 'mt5_bridge_windows.log' -Force -ErrorAction SilentlyContinue"
        if exist "mt5_bridge_windows.log" (
            echo File still locked, renaming to .old...
            ren "mt5_bridge_windows.log" "mt5_bridge_windows.log.old"
        )
    )
    if not exist "mt5_bridge_windows.log" (
        echo ✅ Successfully removed mt5_bridge_windows.log
    )
) else (
    echo ℹ️  mt5_bridge_windows.log not found
)

echo Cleaning up other temporary log files...
del /f /q "test_bridge.log" 2>nul
del /f /q "bridge_test.log" 2>nul
del /f /q "*.log.old" 2>nul

echo ===========================================
echo Ensuring main log file exists...
echo ===========================================

if not exist "mt5_bridge.log" (
    echo Creating main log file: mt5_bridge.log
    echo. > mt5_bridge.log
)

echo ✅ Main log file: mt5_bridge.log
echo ===========================================
echo Cleanup completed!
echo You can now restart the MT5 Bridge
echo ===========================================

pause