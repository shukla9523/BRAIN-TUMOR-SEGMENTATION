@echo off
echo ===================================================
echo Starting NeuroScan AI Platform...
echo ===================================================

cd /d "%~dp0"

echo [1/3] Ensuring sample phantom scans are ready...
python backend\scripts\generate_synthetic_sample.py >nul 2>&1
python backend\scripts\export_evaluation_metrics.py >nul 2>&1

echo [2/3] Launching FastAPI Backend on http://127.0.0.1:8000 ...
start "NeuroScan AI Backend" cmd /k "set PYTHONPATH=backend&& python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

timeout /t 2 /nobreak >nul

echo [3/3] Launching React Vite Frontend on http://localhost:5175 ...
cd frontend
start "NeuroScan AI Frontend" cmd /k "npm run dev"

timeout /t 3 /nobreak >nul

echo Opening browser at http://localhost:5175 ...
start http://localhost:5175

echo ===================================================
echo NeuroScan AI is running!
echo - Web App:     http://localhost:5175
echo - Backend API: http://127.0.0.1:8000/docs
echo ===================================================
