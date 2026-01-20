# PowerShell Verification script for Parser service

Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "Parser Service Verification" -ForegroundColor Cyan
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""

# Check if Python is installed
Write-Host "1. Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "   ✓ $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not found" -ForegroundColor Red
    exit 1
}

# Check if dependencies are installed
Write-Host ""
Write-Host "2. Checking Python dependencies..." -ForegroundColor Yellow

$dependencies = @("kafka", "websockets", "dotenv")
$allInstalled = $true

foreach ($dep in $dependencies) {
    $check = python -c "import $dep" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "   ✓ $dep installed" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $dep not installed" -ForegroundColor Red
        $allInstalled = $false
    }
}

if (-not $allInstalled) {
    Write-Host ""
    Write-Host "   Run: pip install -r requirements.txt" -ForegroundColor Yellow
    exit 1
}

# Check if required files exist
Write-Host ""
Write-Host "3. Checking required files..." -ForegroundColor Yellow
$files = @("main.py", "producer.py", "hl_ws_client.py", "consumer_test.py", "requirements.txt", "env.example")
$allFilesExist = $true

foreach ($file in $files) {
    if (Test-Path $file) {
        Write-Host "   ✓ $file exists" -ForegroundColor Green
    } else {
        Write-Host "   ✗ $file not found" -ForegroundColor Red
        $allFilesExist = $false
    }
}

if (-not $allFilesExist) {
    exit 1
}

# Check if .env file exists
Write-Host ""
Write-Host "4. Checking environment configuration..." -ForegroundColor Yellow
if (Test-Path ".env") {
    Write-Host "   ✓ .env file exists" -ForegroundColor Green
    
    $envContent = Get-Content .env -Raw
    if ($envContent -match "HL_COIN") {
        Write-Host "   ✓ HL_COIN configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ HL_COIN not set in .env" -ForegroundColor Yellow
    }
    
    if ($envContent -match "KAFKA_BOOTSTRAP_SERVERS") {
        Write-Host "   ✓ KAFKA_BOOTSTRAP_SERVERS configured" -ForegroundColor Green
    } else {
        Write-Host "   ⚠ KAFKA_BOOTSTRAP_SERVERS not set in .env" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ⚠ .env file not found (will use defaults)" -ForegroundColor Yellow
    Write-Host "   Create one from env.example: Copy-Item env.example .env" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host "✓ All checks passed!" -ForegroundColor Green
Write-Host "==========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Next steps:" -ForegroundColor Yellow
Write-Host "1. Start Kafka if not running"
Write-Host "2. Run: python main.py"
Write-Host "3. Verify messages: python consumer_test.py"
Write-Host ""
