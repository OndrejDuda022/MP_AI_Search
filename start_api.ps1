# Start the AI Search API server (Windows)

Write-Host "Starting AI Search API..." -ForegroundColor Cyan

# Check if requirements are installed
Write-Host "Checking dependencies..." -ForegroundColor Yellow
pip install -q -r requirements.txt

# Set environment variable if not set
if (-not $env:PYTHONPATH) {
    $env:PYTHONPATH = "."
}

# Start the server
Write-Host ""
Write-Host "Starting server on http://0.0.0.0:8000" -ForegroundColor Green
Write-Host "API docs available at http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""

python -m uvicorn src.api:app --host 0.0.0.0 --port 8000 --reload
