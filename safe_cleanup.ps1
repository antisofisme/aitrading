# SAFE CLEANUP SCRIPT - Only deletes 100% safe files
# Run as Administrator for best results

Write-Host "=== SAFE STORAGE CLEANUP ===" -ForegroundColor Green
Write-Host "This script only deletes 100% safe temporary files" -ForegroundColor Yellow

# Check current space before cleanup
$diskBefore = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGBBefore = [math]::Round($diskBefore.FreeSpace/1GB,2)
Write-Host "`nFree space before cleanup: $freeGBBefore GB" -ForegroundColor Cyan

$totalCleaned = 0

# 1. User Temp folder (SAFEST - 100% safe)
Write-Host "`n1. Cleaning User Temp folder..." -ForegroundColor Yellow
try {
    $tempSizeBefore = (Get-ChildItem -Path $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    Remove-Item -Path "$env:TEMP\*" -Recurse -Force -ErrorAction SilentlyContinue
    $tempSizeAfter = (Get-ChildItem -Path $env:TEMP -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $tempCleaned = [math]::Round(($tempSizeBefore - $tempSizeAfter)/1GB,2)
    $totalCleaned += $tempCleaned
    Write-Host "   Cleaned: $tempCleaned GB" -ForegroundColor Green
} catch {
    Write-Host "   Error cleaning user temp" -ForegroundColor Red
}

# 2. Windows Temp folder (SAFE)
Write-Host "`n2. Cleaning Windows Temp folder..." -ForegroundColor Yellow
try {
    $winTempSizeBefore = (Get-ChildItem -Path "C:\Windows\Temp" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    Remove-Item -Path "C:\Windows\Temp\*" -Recurse -Force -ErrorAction SilentlyContinue
    $winTempSizeAfter = (Get-ChildItem -Path "C:\Windows\Temp" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $winTempCleaned = [math]::Round(($winTempSizeBefore - $winTempSizeAfter)/1GB,2)
    $totalCleaned += $winTempCleaned
    Write-Host "   Cleaned: $winTempCleaned GB" -ForegroundColor Green
} catch {
    Write-Host "   Error cleaning Windows temp (may need admin rights)" -ForegroundColor Yellow
}

# 3. Windows Update Cache (SAFE)
Write-Host "`n3. Cleaning Windows Update cache..." -ForegroundColor Yellow
try {
    $updateSizeBefore = (Get-ChildItem -Path "C:\Windows\SoftwareDistribution\Download" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    Stop-Service -Name "wuauserv" -Force -ErrorAction SilentlyContinue
    Remove-Item -Path "C:\Windows\SoftwareDistribution\Download\*" -Recurse -Force -ErrorAction SilentlyContinue
    Start-Service -Name "wuauserv" -ErrorAction SilentlyContinue
    $updateSizeAfter = (Get-ChildItem -Path "C:\Windows\SoftwareDistribution\Download" -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $updateCleaned = [math]::Round(($updateSizeBefore - $updateSizeAfter)/1GB,2)
    $totalCleaned += $updateCleaned
    Write-Host "   Cleaned: $updateCleaned GB" -ForegroundColor Green
} catch {
    Write-Host "   Error cleaning Windows Update cache (may need admin rights)" -ForegroundColor Yellow
}

# 4. Chrome Cache (SAFE - only cache)
Write-Host "`n4. Cleaning Chrome cache..." -ForegroundColor Yellow
$chromeCachePath = "$env:LOCALAPPDATA\Google\Chrome\User Data\Default\Cache"
if (Test-Path $chromeCachePath) {
    try {
        $chromeSizeBefore = (Get-ChildItem -Path $chromeCachePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        Remove-Item -Path "$chromeCachePath\*" -Recurse -Force -ErrorAction SilentlyContinue
        $chromeSizeAfter = (Get-ChildItem -Path $chromeCachePath -Recurse -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
        $chromeCleaned = [math]::Round(($chromeSizeBefore - $chromeSizeAfter)/1GB,2)
        $totalCleaned += $chromeCleaned
        Write-Host "   Cleaned: $chromeCleaned GB" -ForegroundColor Green
    } catch {
        Write-Host "   Chrome may be running - close Chrome first" -ForegroundColor Yellow
    }
} else {
    Write-Host "   Chrome cache not found" -ForegroundColor Gray
}

# 5. Recycle Bin (SAFE if you're sure)
Write-Host "`n5. Cleaning Recycle Bin..." -ForegroundColor Yellow
try {
    $recycleBinSizeBefore = (Get-ChildItem -Path "C:\`$Recycle.Bin" -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    Clear-RecycleBin -Force -ErrorAction SilentlyContinue
    $recycleBinSizeAfter = (Get-ChildItem -Path "C:\`$Recycle.Bin" -Recurse -Force -ErrorAction SilentlyContinue | Measure-Object -Property Length -Sum).Sum
    $recycleBinCleaned = [math]::Round(($recycleBinSizeBefore - $recycleBinSizeAfter)/1GB,2)
    $totalCleaned += $recycleBinCleaned
    Write-Host "   Cleaned: $recycleBinCleaned GB" -ForegroundColor Green
} catch {
    Write-Host "   Error cleaning Recycle Bin" -ForegroundColor Yellow
}

# Final results
Write-Host "`n=== CLEANUP COMPLETE ===" -ForegroundColor Green
$diskAfter = Get-WmiObject -Class Win32_LogicalDisk -Filter "DeviceID='C:'"
$freeGBAfter = [math]::Round($diskAfter.FreeSpace/1GB,2)
$actualFreed = $freeGBAfter - $freeGBBefore

Write-Host "Free space before: $freeGBBefore GB" -ForegroundColor Cyan
Write-Host "Free space after:  $freeGBAfter GB" -ForegroundColor Cyan
Write-Host "Space freed: $actualFreed GB" -ForegroundColor Green
Write-Host "Estimated cleaned: $totalCleaned GB" -ForegroundColor Yellow

if ($actualFreed -gt 10) {
    Write-Host "`nEXCELLENT! Significant space freed!" -ForegroundColor Green
} elseif ($actualFreed -gt 5) {
    Write-Host "`nGOOD! Some space freed." -ForegroundColor Yellow  
} else {
    Write-Host "`nMay need to check other folders for more cleanup." -ForegroundColor Yellow
}
