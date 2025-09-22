@echo off
echo ===== SAFE STORAGE CLEANUP =====
echo This will clean temporary files safely
echo.

REM Check current free space
echo Checking current disk space...
for /f "tokens=3" %%a in ('dir c:\ /-c ^| find "bytes free"') do set freespace=%%a
echo Current free space: %freespace% bytes
echo.

REM Clean user temp folder (SAFEST)
echo 1. Cleaning user temp folder...
del /q /f /s "%TEMP%\*" 2>nul
for /d %%x in ("%TEMP%\*") do rd /s /q "%%x" 2>nul
echo    User temp cleaned
echo.

REM Clean Windows temp folder
echo 2. Cleaning Windows temp folder...
del /q /f /s "C:\Windows\Temp\*" 2>nul
for /d %%x in ("C:\Windows\Temp\*") do rd /s /q "%%x" 2>nul
echo    Windows temp cleaned
echo.

REM Clean pip cache
echo 3. Cleaning pip cache...
pip cache purge 2>nul
echo    Pip cache cleaned
echo.

REM Clean npm cache
echo 4. Cleaning npm cache...
npm cache clean --force 2>nul
echo    npm cache cleaned
echo.

REM Run disk cleanup
echo 5. Running Windows Disk Cleanup...
cleanmgr /sagerun:1
echo    Disk cleanup completed
echo.

REM Check final free space
echo Checking final disk space...
for /f "tokens=3" %%a in ('dir c:\ /-c ^| find "bytes free"') do set newfreespace=%%a
echo Final free space: %newfreespace% bytes
echo.

echo ===== CLEANUP COMPLETED =====
echo Press any key to exit...
pause >nul
