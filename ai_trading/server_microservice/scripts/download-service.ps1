# Download Wheels for Specific Microservice
# Individual service wheels download

param(
    [Parameter(Mandatory=$true)]
    [string]$Service,
    [switch]$Force = $false,
    [switch]$Quiet = $false
)

# Service validation
$validServices = @("api-gateway", "mt5-bridge", "trading-engine", "ml-processing", 
                   "deep-learning", "ai-orchestration", "ai-provider", "database-service")

if ($Service -notin $validServices) {
    Write-Host "❌ Invalid service: $Service" -ForegroundColor Red
    Write-Host "Valid services: $($validServices -join ', ')" -ForegroundColor Yellow
    exit 1
}

Write-Host "🚀 Downloading wheels for: $Service" -ForegroundColor Green
Write-Host "=" * 50

$wheelsDir = "wheels\$Service"
$serviceDir = "services\$Service"
$requirementsFile = "$serviceDir\requirements.txt"
$pyprojectFile = "$serviceDir\pyproject.toml"

# Check if pyproject.toml exists
if (!(Test-Path $pyprojectFile)) {
    Write-Host "❌ pyproject.toml not found in $serviceDir" -ForegroundColor Red
    Write-Host "Please create Poetry configuration first" -ForegroundColor Yellow
    exit 1
}

# Check if already downloaded
if (!$Force -and (Get-ChildItem -Path $wheelsDir -Filter "*.whl" -ErrorAction SilentlyContinue).Count -gt 0) {
    $files = Get-ChildItem -Path $wheelsDir -Recurse -File -ErrorAction SilentlyContinue
    $existingSize = if ($files) {
        [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    } else { 0 }
    Write-Host "⚠️ $Service already has wheels (${existingSize}MB)" -ForegroundColor Yellow
    Write-Host "Use -Force to re-download" -ForegroundColor Yellow
    exit 0
}

$startTime = Get-Date

try {
    # Step 1: Export Poetry dependencies
    Write-Host "📤 Exporting Poetry dependencies..." -ForegroundColor Cyan
    Push-Location $serviceDir
    
    if (Get-Command poetry -ErrorAction SilentlyContinue) {
        & poetry export -f requirements.txt --output requirements.txt --without-hashes
        if ($LASTEXITCODE -ne 0) {
            Write-Host "⚠️ Poetry export failed, using existing requirements.txt" -ForegroundColor Yellow
        } else {
            Write-Host "✅ Poetry dependencies exported" -ForegroundColor Green
        }
    } else {
        Write-Host "⚠️ Poetry not found, using existing requirements.txt" -ForegroundColor Yellow
    }
    
    Pop-Location
    
    # Verify requirements.txt exists
    if (!(Test-Path $requirementsFile)) {
        Write-Host "❌ requirements.txt not found after export" -ForegroundColor Red
        exit 1
    }
    
    # Step 2: Create wheels directory
    Write-Host "📁 Creating wheels directory..." -ForegroundColor Cyan
    New-Item -ItemType Directory -Path $wheelsDir -Force | Out-Null
    
    # Step 3: Download wheels
    Write-Host "📦 Downloading wheels..." -ForegroundColor Cyan
    
    $pipArgs = @(
        "wheel"
        "-r", $requirementsFile
        "-w", $wheelsDir
        "--only-binary=:all:"
        "--disable-pip-version-check"
        "--prefer-binary"
    )
    
    if ($Quiet) {
        $pipArgs += "--quiet"
    } else {
        $pipArgs += "--verbose"
    }
    
    & pip @pipArgs
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Wheel download failed with exit code $LASTEXITCODE" -ForegroundColor Red
        exit 1
    }
    
    # Step 4: Filter for Linux compatibility (if needed)
    Write-Host "🔍 Filtering Linux-compatible wheels..." -ForegroundColor Cyan
    $allWheels = Get-ChildItem -Path $wheelsDir -Filter "*.whl"
    $linuxWheels = $allWheels | Where-Object {
        $_.Name -match "linux_x86_64|py3-none-any|cp311-cp311-linux|py2\.py3-none-any|py311-none-any"
    }
    
    $filteredCount = $allWheels.Count - $linuxWheels.Count
    if ($filteredCount -gt 0) {
        Write-Host "⚠️ Removed $filteredCount non-Linux wheels" -ForegroundColor Yellow
        
        # Remove non-Linux wheels
        $allWheels | Where-Object { $_ -notin $linuxWheels } | Remove-Item -Force
    }
    
    # Step 5: Report results
    $elapsed = ((Get-Date) - $startTime).TotalSeconds
    $wheelCount = (Get-ChildItem -Path $wheelsDir -Filter "*.whl" -ErrorAction SilentlyContinue).Count
    $files = Get-ChildItem -Path $wheelsDir -Recurse -File -ErrorAction SilentlyContinue
    $totalSize = if ($files) {
        [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
    } else { 0 }
    
    Write-Host ""
    Write-Host "🎉 SUCCESS: $Service wheels downloaded!" -ForegroundColor Green
    Write-Host "   Time taken: $([math]::Round($elapsed, 1)) seconds" -ForegroundColor White
    Write-Host "   Total size: ${totalSize}MB" -ForegroundColor White  
    Write-Host "   Linux wheels: $wheelCount" -ForegroundColor White
    Write-Host "   Location: $wheelsDir" -ForegroundColor White
    
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "  1. docker-compose build $Service" -ForegroundColor White
    Write-Host "  2. docker-compose up $Service" -ForegroundColor White
    
} catch {
    Write-Host "❌ Error downloading wheels: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}