@echo off
echo ===========================================
echo Simple Log Cleanup
echo ===========================================

echo Handling locked log files...

if exist "mt5_bridge_windows.log" (
    echo Renaming locked file to .old...
    ren "mt5_bridge_windows.log" "mt5_bridge_windows.log.old" 2>nul
    if exist "mt5_bridge_windows.log.old" (
        echo ✅ Renamed to mt5_bridge_windows.log.old
    )
)

echo Cleaning up other log files...
del /f /q "test_bridge.log" 2>nul
del /f /q "bridge_test.log" 2>nul

echo ===========================================
echo Log Status:
echo ===========================================

if exist "mt5_bridge.log" (
    echo ✅ Main log file: mt5_bridge.log
) else (
    echo Creating main log file...
    echo. > mt5_bridge.log
    echo ✅ Created: mt5_bridge.log
)

if exist "mt5_bridge_windows.log.old" (
    echo ⚠️  Old file: mt5_bridge_windows.log.old (can be safely deleted later)
)

echo ===========================================
echo ✅ Cleanup completed!
echo Main log file: mt5_bridge.log
echo ===========================================

pause