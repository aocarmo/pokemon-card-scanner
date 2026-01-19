# Pokemon Card Scanner - Start Script
# Run: .\start.ps1

$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# Backend
Write-Host "Starting Backend..." -ForegroundColor Cyan
$backendPath = Join-Path $ProjectRoot "backend"

if (-not (Test-Path (Join-Path $backendPath "venv"))) {
    Write-Host "Creating virtual environment..." -ForegroundColor Yellow
    python -m venv (Join-Path $backendPath "venv")
}

$activateScript = Join-Path $backendPath "venv\Scripts\Activate.ps1"
& $activateScript

Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install fastapi uvicorn python-multipart opencv-python easyocr numpy --quiet

Set-Location (Join-Path $backendPath "src")
Start-Process powershell -ArgumentList "-NoExit", "-Command", "& '$activateScript'; python -m uvicorn api.app:app --reload --host 0.0.0.0 --port 8000"

# Frontend
Write-Host "Starting Frontend..." -ForegroundColor Cyan
$frontendPath = Join-Path $ProjectRoot "frontend"
Set-Location $frontendPath

if (-not (Test-Path "node_modules")) {
    Write-Host "Installing npm packages..." -ForegroundColor Yellow
    npm install
}

Start-Process powershell -ArgumentList "-NoExit", "-Command", "Set-Location '$frontendPath'; npm start"

Write-Host "`nServices starting:" -ForegroundColor Green
Write-Host "  Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "  Frontend: http://localhost:3000" -ForegroundColor White
Write-Host "`nPress any key to exit this window..."
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
