@echo off
echo ===========================================
echo Cleaning up duplicate log files
echo ===========================================

echo Removing duplicate log files...
if exist "mt5_bridge_windows.log" (
    del "mt5_bridge_windows.log"
    echo ✅ Removed mt5_bridge_windows.log
) else (
    echo ℹ️  mt5_bridge_windows.log not found
)

if exist "test_bridge.log" (
    del "test_bridge.log"
    echo ✅ Removed test_bridge.log
) else (
    echo ℹ️  test_bridge.log not found
)

if exist "bridge_test.log" (
    del "bridge_test.log"
    echo ✅ Removed bridge_test.log
) else (
    echo ℹ️  bridge_test.log not found
)

echo ===========================================
echo Checking main log file...
echo ===========================================

if exist "mt5_bridge.log" (
    echo ✅ Main log file exists: mt5_bridge.log
) else (
    echo ℹ️  Creating main log file: mt5_bridge.log
    echo. > mt5_bridge.log
)

echo ===========================================
echo Log cleanup completed!
echo Main log file: mt5_bridge.log
echo ===========================================

pause