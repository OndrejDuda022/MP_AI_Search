# Selenium Docker Container Startup Script
# Automatically checks and starts Selenium container if needed

$CONTAINER_NAME = "selenium-chrome"
$IMAGE_NAME = "selenium/standalone-chrome:latest"
$PORT = "4444"

Write-Host "[*] Checking Selenium Docker container status..." -ForegroundColor Cyan

# Check if Docker is running
try {
    docker ps | Out-Null
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
        exit 1
    }
} catch {
    Write-Host "[!] Docker is not installed or not running." -ForegroundColor Red
    exit 1
}

# Check if container is already running
$running = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if ($running -eq $CONTAINER_NAME) {
    Write-Host "[+] Selenium container is already running." -ForegroundColor Green
    Write-Host "[*] Container URL: http://localhost:$PORT/wd/hub" -ForegroundColor Cyan
    exit 0
}

# Check if container exists but is stopped
$stopped = docker ps -a --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if ($stopped -eq $CONTAINER_NAME) {
    Write-Host "[*] Starting existing Selenium container..." -ForegroundColor Yellow
    docker start $CONTAINER_NAME
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[+] Selenium container started successfully." -ForegroundColor Green
        Write-Host "[*] Container URL: http://localhost:$PORT/wd/hub" -ForegroundColor Cyan
        exit 0
    } else {
        Write-Host "[!] Failed to start container. Removing and recreating..." -ForegroundColor Yellow
        docker rm $CONTAINER_NAME
    }
}

# Check if image exists
$imageExists = docker images --filter "reference=$IMAGE_NAME" --format "{{.Repository}}"
if (-not $imageExists) {
    Write-Host "[*] Pulling Selenium image (this may take a few minutes)..." -ForegroundColor Yellow
    docker pull $IMAGE_NAME
    if ($LASTEXITCODE -ne 0) {
        Write-Host "[!] Failed to pull Docker image." -ForegroundColor Red
        exit 1
    }
}

# Create and start new container
Write-Host "[*] Creating new Selenium container..." -ForegroundColor Yellow
docker run `
    --name $CONTAINER_NAME `
    --detach `
    --rm `
    --publish "${PORT}:4444" `
    --shm-size=1g `
    --cpus="1.5" `
    --memory="1g" `
    --security-opt no-new-privileges `
    --pids-limit 512 `
    $IMAGE_NAME

if ($LASTEXITCODE -eq 0) {
    Write-Host "[+] Selenium container created and started successfully!" -ForegroundColor Green
    Write-Host "[*] Container URL: http://localhost:$PORT/wd/hub" -ForegroundColor Cyan
    Write-Host "[*] Add to .env file: SELENIUM_REMOTE_URL=http://localhost:$PORT/wd/hub" -ForegroundColor Cyan
} else {
    Write-Host "[!] Failed to create Selenium container." -ForegroundColor Red
    exit 1
}
