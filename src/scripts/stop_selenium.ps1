# Stop Selenium Docker Container Script

$CONTAINER_NAME = "selenium-chrome"

Write-Host "[*] Stopping Selenium container..." -ForegroundColor Cyan

$running = docker ps --filter "name=$CONTAINER_NAME" --format "{{.Names}}"
if ($running -eq $CONTAINER_NAME) {
    docker stop $CONTAINER_NAME
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[+] Selenium container stopped successfully." -ForegroundColor Green
    } else {
        Write-Host "[!] Failed to stop container." -ForegroundColor Red
        exit 1
    }
} else {
    Write-Host "[*] Selenium container is not running." -ForegroundColor Yellow
}
