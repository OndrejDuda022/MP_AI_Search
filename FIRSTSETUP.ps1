#AI Search Engine - One-shot setup script (Windows / PowerShell), made additionally (not a part of the maturita project)
#Run from the project root: .\FIRSTSETUP.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "`n[*] AI Search Engine - Setup" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

# 1. Python availability
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Cyan
try {
    $pyVersion = python --version 2>&1
    Write-Host "    Found: $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "[!] Python not found. Install Python 3.8+ from https://python.org and try again." -ForegroundColor Red
    exit 1
}

# 2. Virtual environment
$VenvDir = Join-Path $ProjectRoot ".venv"
Write-Host "`n[2/6] Setting up virtual environment..." -ForegroundColor Cyan

if (Test-Path $VenvDir) {
    Write-Host "Virtual environment already exists at .venv — skipping creation." -ForegroundColor Yellow
} else {
    python -m venv $VenvDir
    Write-Host "Created virtual environment at .venv" -ForegroundColor Green
}

$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

# 3. Install dependencies
Write-Host "`n[3/6] Installing dependencies..." -ForegroundColor Cyan
& $PipExe install --upgrade pip --quiet
& $PipExe install -r (Join-Path $ProjectRoot "requirements.txt")
Write-Host "Dependencies installed." -ForegroundColor Green

# 4. Environment file
$EnvFile    = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"
Write-Host "`n[4/6] Configuring environment file..." -ForegroundColor Cyan

if (Test-Path $EnvFile) {
    Write-Host ".env already exists — keeping it unchanged." -ForegroundColor Yellow
} else {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "Created .env from .env.example" -ForegroundColor Green
        Write-Host "!! Open .env and fill in your API keys before running the app." -ForegroundColor Yellow
    } else {
        Write-Host "[!] .env.example not found. Create a .env file manually (see README)." -ForegroundColor Red
    }
}

# 5. Embedding model
$ModelName  = "paraphrase-multilingual-mpnet-base-v2"
$ModelDest  = Join-Path $ProjectRoot "models\$ModelName"
Write-Host "`n[5/6] Setting up embedding model..." -ForegroundColor Cyan

if (Test-Path $ModelDest) {
    Write-Host "Embedding model already present at models\$ModelName" -ForegroundColor Yellow
} else {
    Write-Host "Downloading embedding model from Hugging Face (one-time, ~1 GB)..." -ForegroundColor Cyan
    $PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
    & $PythonExe -c @"
from sentence_transformers import SentenceTransformer
dest = r'$ModelDest'
print(f'Saving to {dest}')
m = SentenceTransformer('$ModelName')
m.save(dest)
print('Model saved.')
"@
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Model downloaded and saved." -ForegroundColor Green
    } else {
        Write-Host "[!] Model download failed. Check your internet connection and re-run the script." -ForegroundColor Red
        exit 1
    }
}

# 6. Selenium (optional)
Write-Host "`n[6/6] Selenium / Docker (optional)..." -ForegroundColor Cyan
$dockerAvailable = $false
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -eq 0) { $dockerAvailable = $true }
} catch {}

if ($dockerAvailable) {
    $answer = Read-Host "Docker is available. Start the Selenium container now? [y/N]"
    if ($answer -match "^[Yy]$") {
        $PythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
        & $PythonExe -c @"
import sys, os
sys.path.insert(0, r'$ProjectRoot\src')
from docker_manager import ensure_selenium_container
ok = ensure_selenium_container()
sys.exit(0 if ok else 1)
"@
        if ($LASTEXITCODE -eq 0) {
            Write-Host "[+] Selenium container is ready." -ForegroundColor Green
            Write-Host "Add SELENIUM_REMOTE_URL=http://localhost:4444/wd/hub to your .env" -ForegroundColor Yellow
        } else {
            Write-Host "[!] Selenium container could not be started. Check Docker and try again." -ForegroundColor Red
        }
    } else {
        Write-Host "Skipped. You can start Selenium later via docker_manager.ensure_selenium_container()." -ForegroundColor Yellow
    }
} else {
    Write-Host "Docker not detected — Selenium will use local ChromeDriver (webdriver-manager)." -ForegroundColor Yellow
}

# Done
Write-Host "[+] Setup complete!" -ForegroundColor Green
Write-Host "Activate the virtual environment: .venv\Scripts\Activate.ps1"
Write-Host "Run the app: python src\main.py"
