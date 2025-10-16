# Quick Docker Status Check Script

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Docker Status Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "Checking Docker installation..." -ForegroundColor Yellow

try {
    $dockerVersion = docker --version
    Write-Host "✓ Docker installed: $dockerVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Docker not found. Please install Docker Desktop." -ForegroundColor Red
    Write-Host "  Download: https://www.docker.com/products/docker-desktop" -ForegroundColor Yellow
    exit 1
}

Write-Host ""
Write-Host "Checking Docker daemon..." -ForegroundColor Yellow

try {
    $dockerInfo = docker info 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Docker Desktop is running" -ForegroundColor Green
        Write-Host ""
        Write-Host "========================================" -ForegroundColor Green
        Write-Host "  Ready to start services!" -ForegroundColor Green
        Write-Host "========================================" -ForegroundColor Green
        Write-Host ""
        Write-Host "Next step: Run the following command" -ForegroundColor Yellow
        Write-Host "  docker-compose up --build" -ForegroundColor White
    } else {
        throw "Docker daemon not running"
    }
} catch {
    Write-Host "✗ Docker Desktop is NOT running" -ForegroundColor Red
    Write-Host ""
    Write-Host "Please:" -ForegroundColor Yellow
    Write-Host "  1. Start Docker Desktop application" -ForegroundColor White
    Write-Host "  2. Wait for status 'Docker Desktop is running'" -ForegroundColor White
    Write-Host "  3. Run this script again" -ForegroundColor White
    Write-Host ""
    exit 1
}


