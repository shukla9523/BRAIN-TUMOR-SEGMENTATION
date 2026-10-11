# NeuroScan AI Platform Startup Script for PowerShell
Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  Starting NeuroScan AI Platform" -ForegroundColor Cyan
Write-Host "===================================================" -ForegroundColor Cyan

$WorkspaceRoot = $PSScriptRoot

# 1. Ensure sample scan and metrics exist
Write-Host "[1/3] Verifying sample phantoms and evaluation metrics..." -ForegroundColor Yellow
python "$WorkspaceRoot\backend\scripts\generate_synthetic_sample.py"
python "$WorkspaceRoot\backend\scripts\export_evaluation_metrics.py"

# 2. Launch FastAPI Backend
Write-Host "[2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "`$env:PYTHONPATH='backend'; python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload" -WorkingDirectory $WorkspaceRoot

Start-Sleep -Seconds 2

# 3. Launch React Vite Frontend
Write-Host "[3/3] Launching React Vite Frontend on http://localhost:5175 ..." -ForegroundColor Green
Start-Process powershell -ArgumentList "-NoExit", "-Command", "npm run dev" -WorkingDirectory "$WorkspaceRoot\frontend"

Start-Sleep -Seconds 3

# 4. Open default web browser
Start-Process "http://localhost:5175"

Write-Host "===================================================" -ForegroundColor Cyan
Write-Host "  NeuroScan AI is now actively running!" -ForegroundColor Cyan
Write-Host "  Frontend Web UI:   http://localhost:5175" -ForegroundColor White
Write-Host "  Backend Swagger:   http://127.0.0.1:8000/docs" -ForegroundColor White
Write-Host "===================================================" -ForegroundColor Cyan
