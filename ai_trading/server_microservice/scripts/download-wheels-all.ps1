# Download Wheels for All Microservices
# Hybrid Poetry + Offline Wheels Strategy

param(
    [switch]$Force = $false,
    [switch]$Quiet = $false
)

Write-Host "🚀 AI Trading Platform - Microservices Wheels Download" -ForegroundColor Green
Write-Host "Strategy: Poetry Export → Offline Wheels → Fast Docker Builds" -ForegroundColor Cyan
Write-Host "=" * 70

# Service configuration with tiers and expected sizes (CORRECTED)
$services = @{
    # TIER 1: Core Services (< 50MB)
    "api-gateway" = @{
        tier = "tier1"
        description = "API Gateway - FastAPI + Auth + Routing"
        max_size = "50MB"
        priority = 1
    }
    "user-service" = @{
        tier = "tier1"
        description = "User Service - Authentication + Sessions" 
        max_size = "50MB"
        priority = 1
    }
    "database-service" = @{
        tier = "tier1"
        description = "Database Service - Multi-DB drivers"
        max_size = "100MB"
        priority = 1
    }
    
    # TIER 2: Data Services (< 200MB)
    "data-bridge" = @{
        tier = "tier2"
        description = "Data Bridge - Real-time market data"
        max_size = "150MB"
        priority = 2
    }
    "trading-engine" = @{
        tier = "tier2"
        description = "Trading Engine - Basic ML + TA-Lib"
        max_size = "200MB"
        priority = 2
    }
    
    # TIER 3: AI Basic (< 500MB)
    "ai-provider" = @{
        tier = "tier3"
        description = "AI Provider - LiteLLM + Langfuse"
        max_size = "300MB"
        priority = 3
    }
    
    # TIER 4: AI Advanced (< 2GB)
    "ai-orchestration" = @{
        tier = "tier4"
        description = "AI Orchestration - LangChain + Workflows"
        max_size = "800MB"
        priority = 4
    }
    "ml-processing" = @{
        tier = "tier4"
        description = "ML Processing - Scikit-learn + Traditional ML"
        max_size = "1000MB"
        priority = 4
    }
    
    # TIER 5: ML Heavy (< 4GB)
    "deep-learning" = @{
        tier = "tier5"
        description = "Deep Learning - PyTorch + Transformers"
        max_size = "2000MB"
        priority = 5
    }
}

function Download-ServiceWheels {
    param($ServiceName, $ServiceConfig)
    
    $wheelsDir = "wheels\$ServiceName"
    $serviceDir = "services\$ServiceName"
    $requirementsFile = "$serviceDir\requirements.txt"
    $pyprojectFile = "$serviceDir\pyproject.toml"
    
    Write-Host "[SERVICE] Processing $ServiceName..." -ForegroundColor $ServiceConfig.tier
    Write-Host "   Description: $($ServiceConfig.description)" -ForegroundColor White
    Write-Host "   Expected Size: $($ServiceConfig.max_size)" -ForegroundColor White
    Write-Host "   Target: $wheelsDir\" -ForegroundColor White
    
    # Check if pyproject.toml exists
    if (!(Test-Path $pyprojectFile)) {
        Write-Host "   [ERROR] pyproject.toml not found in $serviceDir" -ForegroundColor Red
        return $false
    }
    
    # Check if already downloaded (unless force)
    if (!$Force -and (Get-ChildItem -Path $wheelsDir -Filter "*.whl" -ErrorAction SilentlyContinue).Count -gt 0) {
        $files = Get-ChildItem -Path $wheelsDir -Recurse -File -ErrorAction SilentlyContinue
        $existingSize = if ($files) {
            [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
        } else { 0 }
        Write-Host "   [SKIP] Already has wheels (${existingSize}MB)" -ForegroundColor Yellow
        Write-Host "   Use -Force to re-download" -ForegroundColor Yellow
        return $true
    }
    
    $startTime = Get-Date
    
    try {
        # Step 1: Export Poetry dependencies
        Write-Host "   [EXPORT] Exporting Poetry dependencies..." -ForegroundColor Cyan
        Push-Location $serviceDir
        
        if (Get-Command poetry -ErrorAction SilentlyContinue) {
            & poetry export -f requirements.txt --output requirements.txt --without-hashes
            if ($LASTEXITCODE -ne 0) {
                Write-Host "   [WARN] Poetry export failed, using existing requirements.txt" -ForegroundColor Yellow
            }
        } else {
            Write-Host "   [WARN] Poetry not found, using existing requirements.txt" -ForegroundColor Yellow
        }
        
        Pop-Location
        
        # Step 2: Download wheels
        Write-Host "   [DOWNLOAD] Downloading wheels..." -ForegroundColor Cyan
        New-Item -ItemType Directory -Path $wheelsDir -Force | Out-Null
        
        $pipArgs = @(
            "wheel"
            "-r", $requirementsFile
            "-w", $wheelsDir
            "--only-binary=:all:"
            "--disable-pip-version-check"
        )
        
        if ($Quiet) {
            $pipArgs += "--quiet"
        }
        
        & pip @pipArgs
        
        if ($LASTEXITCODE -ne 0) {
            Write-Host "   [FAIL] Wheel download failed with exit code $LASTEXITCODE" -ForegroundColor Red
            return $false
        }
        
        # Step 3: Verify and report
        $elapsed = ((Get-Date) - $startTime).TotalSeconds
        $wheelCount = (Get-ChildItem -Path $wheelsDir -Filter "*.whl" -ErrorAction SilentlyContinue).Count
        $files = Get-ChildItem -Path $wheelsDir -Recurse -File -ErrorAction SilentlyContinue
        $totalSize = if ($files) {
            [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
        } else { 0 }
        
        Write-Host "   [SUCCESS] $ServiceName completed!" -ForegroundColor Green
        Write-Host "   Time: $([math]::Round($elapsed, 1))s | Size: ${totalSize}MB | Wheels: $wheelCount" -ForegroundColor White
        Write-Host ""
        
        return $true
        
    } catch {
        Write-Host "   [ERROR] $ServiceName failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Show-Summary {
    param([array]$SuccessfulServices, [array]$FailedServices, [double]$TotalTime)
    
    Write-Host "=" * 70
    Write-Host "📊 DOWNLOAD SUMMARY" -ForegroundColor Green
    Write-Host "   Total time: $([math]::Round($TotalTime, 1)) seconds ($([math]::Round($TotalTime/60, 1)) minutes)" -ForegroundColor White
    Write-Host "   Successful: $($SuccessfulServices.Count) services" -ForegroundColor White
    Write-Host "   Failed: $($FailedServices.Count) services" -ForegroundColor White
    
    if ($SuccessfulServices.Count -gt 0) {
        Write-Host "   ✅ Success: $($SuccessfulServices -join ', ')" -ForegroundColor Green
    }
    
    if ($FailedServices.Count -gt 0) {
        Write-Host "   ❌ Failed: $($FailedServices -join ', ')" -ForegroundColor Red
    }
    
    # Storage breakdown
    Write-Host "`n📦 STORAGE BREAKDOWN:" -ForegroundColor Yellow
    $totalSize = 0
    $totalWheels = 0
    
    foreach ($serviceName in $SuccessfulServices) {
        $wheelsDir = "wheels\$serviceName"
        if (Test-Path $wheelsDir) {
            $wheelCount = (Get-ChildItem -Path $wheelsDir -Filter "*.whl" -ErrorAction SilentlyContinue).Count
            $files = Get-ChildItem -Path $wheelsDir -Recurse -File -ErrorAction SilentlyContinue
            $serviceSize = if ($files) {
                [math]::Round(($files | Measure-Object -Property Length -Sum).Sum / 1MB, 1)
            } else { 0 }
            $totalSize += $serviceSize
            $totalWheels += $wheelCount
            Write-Host "   $serviceName: ${serviceSize}MB ($wheelCount wheels)" -ForegroundColor White
        }
    }
    
    Write-Host "   TOTAL: ${totalSize}MB ($totalWheels wheels)" -ForegroundColor Cyan
    
    # Deployment status
    if ($SuccessfulServices.Count -eq $services.Count) {
        Write-Host "`n🎉 ALL SERVICES READY! Offline deployment enabled!" -ForegroundColor Green
        Write-Host "Next steps:" -ForegroundColor White
        Write-Host "  1. docker-compose build (uses offline wheels)" -ForegroundColor White
        Write-Host "  2. docker-compose up (fast deployment)" -ForegroundColor White
    } elseif ($SuccessfulServices.Count -gt 0) {
        Write-Host "`n⚠️ PARTIAL SUCCESS - Can deploy: $($SuccessfulServices -join ', ')" -ForegroundColor Yellow
    } else {
        Write-Host "`n❌ NO SERVICES READY - Check Poetry configs and internet connection" -ForegroundColor Red
    }
}

# Main execution
$startTime = Get-Date
$successfulServices = @()
$failedServices = @()

Write-Host "🔄 Processing $($services.Count) microservices..." -ForegroundColor Green
Write-Host ""

# Process services by priority (tier1 first, then tier2, etc.)
$sortedServices = $services.GetEnumerator() | Sort-Object {$_.Value.priority}, {$_.Key}

foreach ($serviceEntry in $sortedServices) {
    $serviceName = $serviceEntry.Key
    $serviceConfig = $serviceEntry.Value
    
    $success = Download-ServiceWheels -ServiceName $serviceName -ServiceConfig $serviceConfig
    
    if ($success) {
        $successfulServices += $serviceName
    } else {
        $failedServices += $serviceName
        # Continue with other services even if one fails
    }
}

# Show final summary
$totalTime = ((Get-Date) - $startTime).TotalSeconds
Show-Summary -SuccessfulServices $successfulServices -FailedServices $failedServices -TotalTime $totalTime

# Exit with appropriate code
if ($successfulServices.Count -gt 0) {
    exit 0
} else {
    exit 1
}