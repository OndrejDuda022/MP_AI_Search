# AI Search Engine - one-shot setup script (Windows / PowerShell)
# Run from project root: .\FIRSTSETUP.ps1

$ErrorActionPreference = "Stop"
$ProjectRoot = $PSScriptRoot

Write-Host "`n[*] AI Search Engine - Setup" -ForegroundColor Cyan
Write-Host "Project root: $ProjectRoot"

function Get-SystemPython {
    $candidates = @(
        @("python"),
        @("py", "-3"),
        @("py")
    )

    foreach ($candidate in $candidates) {
        $exe = $candidate[0]
        if (-not (Get-Command $exe -ErrorAction SilentlyContinue)) {
            continue
        }

        $candidateParams = @()
        if ($candidate.Count -gt 1) {
            $candidateParams = $candidate[1..($candidate.Count - 1)]
        }

        try {
            & $exe @candidateParams -c "import sys; print(sys.version)" | Out-Null
            if ($LASTEXITCODE -eq 0) {
                return [PSCustomObject]@{
                    Exe = $exe
                    Params = $candidateParams
                }
            }
        } catch {
            # Try next candidate.
        }
    }

    return $null
}

# 1. Python availability
Write-Host "[1/6] Checking Python installation..." -ForegroundColor Cyan
$SystemPython = Get-SystemPython
if (-not $SystemPython) {
    Write-Host "[!] Python not found. Install Python 3.8+ from https://python.org and try again." -ForegroundColor Red
    exit 1
}

try {
    $SystemPythonExe = $SystemPython.Exe
    $SystemPythonArgs = @($SystemPython.Params)
    $pyVersion = & $SystemPythonExe @SystemPythonArgs --version 2>&1
    if ($LASTEXITCODE -ne 0) {
        throw "Python version check returned non-zero exit code"
    }
    Write-Host "    Found: $($pyVersion | Out-String)" -ForegroundColor Green
} catch {
    Write-Host "[!] Python launcher detected but version check failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
}

# 2. Virtual environment
$DotVenvDir = Join-Path $ProjectRoot ".venv"
$LegacyVenvDir = Join-Path $ProjectRoot "venv"

if (Test-Path $DotVenvDir) {
    $VenvDir = $DotVenvDir
    $VenvLabel = ".venv"
} elseif (Test-Path $LegacyVenvDir) {
    $VenvDir = $LegacyVenvDir
    $VenvLabel = "venv"
} else {
    $VenvDir = $DotVenvDir
    $VenvLabel = ".venv"
}

Write-Host "`n[2/6] Setting up virtual environment..." -ForegroundColor Cyan
if (Test-Path $VenvDir) {
    Write-Host "Virtual environment already exists at $VenvLabel - skipping creation." -ForegroundColor Yellow
} else {
    & $SystemPythonExe @SystemPythonArgs -m venv $VenvDir
    Write-Host "Created virtual environment at $VenvLabel" -ForegroundColor Green
}

$PythonExe = Join-Path $VenvDir "Scripts\python.exe"
$PipExe = Join-Path $VenvDir "Scripts\pip.exe"

if (-not (Test-Path $PythonExe) -or -not (Test-Path $PipExe)) {
    Write-Host "[!] Virtual environment seems incomplete at '$VenvDir'. Delete it and run the script again." -ForegroundColor Red
    exit 1
}

# 3. Install dependencies
Write-Host "`n[3/6] Installing dependencies..." -ForegroundColor Cyan
$RequirementsFile = Join-Path $ProjectRoot "requirements.txt"
if (-not (Test-Path $RequirementsFile)) {
    Write-Host "[!] requirements.txt not found at project root." -ForegroundColor Red
    exit 1
}

& $PipExe install --upgrade pip
& $PipExe install -r $RequirementsFile
Write-Host "Dependencies installed." -ForegroundColor Green

# 4. Environment file
$EnvFile = Join-Path $ProjectRoot ".env"
$EnvExample = Join-Path $ProjectRoot ".env.example"
Write-Host "`n[4/6] Configuring environment file..." -ForegroundColor Cyan

if (Test-Path $EnvFile) {
    Write-Host ".env already exists - keeping it unchanged." -ForegroundColor Yellow
} else {
    if (Test-Path $EnvExample) {
        Copy-Item $EnvExample $EnvFile
        Write-Host "Created .env from .env.example" -ForegroundColor Green
        Write-Host "!! Open .env and fill in API credentials before running searches." -ForegroundColor Yellow
    } else {
        Write-Host "[!] .env.example not found. Create a .env file manually (see README)." -ForegroundColor Red
    }
}

# 5. Embedding model
$ModelName = "paraphrase-multilingual-mpnet-base-v2"
$ModelDest = Join-Path $ProjectRoot "models\$ModelName"
$ModelRequiredFiles = @(
    "config.json",
    "model.safetensors",
    "tokenizer.json"
)

Write-Host "`n[5/6] Setting up embedding model..." -ForegroundColor Cyan
$modelReady = $true
foreach ($file in $ModelRequiredFiles) {
    if (-not (Test-Path (Join-Path $ModelDest $file))) {
        $modelReady = $false
        break
    }
}

if ($modelReady) {
    Write-Host "Embedding model already present at models\$ModelName" -ForegroundColor Yellow
} else {
    Write-Host "Downloading embedding model from Hugging Face (one-time, large download)..." -ForegroundColor Cyan
    & $PythonExe -c @"
from sentence_transformers import SentenceTransformer
from pathlib import Path

dest = Path(r'$ModelDest')
dest.parent.mkdir(parents=True, exist_ok=True)
print(f'Saving model to: {dest}')
model = SentenceTransformer('$ModelName')
model.save(str(dest))
print('Model saved.')
"@
    if ($LASTEXITCODE -eq 0) {
        Write-Host "Model downloaded and saved." -ForegroundColor Green
    } else {
        Write-Host "[!] Model download failed. Check internet connectivity and re-run the script." -ForegroundColor Red
        exit 1
    }
}

# 6. Selenium (optional)
Write-Host "`n[6/6] Selenium / Docker setup (optional)..." -ForegroundColor Cyan
$dockerAvailable = $false
try {
    docker info | Out-Null
    if ($LASTEXITCODE -eq 0) {
        $dockerAvailable = $true
    }
} catch {
    $dockerAvailable = $false
}

if ($dockerAvailable) {
    $answer = Read-Host "Docker is available. Start Selenium container now? [y/N]"
    if ($answer -match "^[Yy]$") {
        & $PythonExe -c @"
import os
import sys

project_root = r'$ProjectRoot'
sys.path.insert(0, project_root)
from src.docker_manager import ensure_selenium_container

ok = ensure_selenium_container()
sys.exit(0 if ok else 1)
"@

        if ($LASTEXITCODE -eq 0) {
            Write-Host "[+] Selenium container is ready." -ForegroundColor Green
            Write-Host "Tip: keep SELENIUM_REMOTE_URL empty in local .env to allow fallback behavior." -ForegroundColor Yellow
        } else {
            Write-Host "[!] Selenium container could not be started. Check Docker and try again." -ForegroundColor Red
        }
    } else {
        Write-Host "Skipped. You can start Selenium later using src.docker_manager.ensure_selenium_container()." -ForegroundColor Yellow
    }
} else {
    Write-Host "Docker not detected or daemon unavailable - app can still use local ChromeDriver fallback." -ForegroundColor Yellow
}

# Done
Write-Host "`n[+] Setup complete!" -ForegroundColor Green
Write-Host "Activate virtual environment: $VenvLabel\Scripts\Activate.ps1"
Write-Host "Start API server after activation: .\start_api.ps1"
Write-Host "Direct API start (without activation): $VenvLabel\Scripts\python.exe -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload"
Write-Host "Or run CLI mode: $VenvLabel\Scripts\python.exe src\main.py"
