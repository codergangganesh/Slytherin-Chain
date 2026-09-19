# SentinelChain — Local Native Startup Script (Without Docker)
Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "   Starting SentinelChain Locally (Without Docker)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

# 1. Start Backend in new terminal window
Write-Host "`n[1/2] Launching Backend API on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\backend'; pip install -e .; python -m uvicorn app.main:create_app --reload --port 8000 --factory"

# 2. Start Frontend in new terminal window
Write-Host "`n[2/2] Launching Frontend Web Console on http://localhost:5173 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd '$PSScriptRoot\frontend'; npm install; npm run dev"

Write-Host "`n==========================================================" -ForegroundColor Green
Write-Host "   SentinelChain is starting!" -ForegroundColor Green
Write-Host "   Web UI:    http://localhost:5173" -ForegroundColor Green
Write-Host "   API Docs:  http://localhost:8000/docs" -ForegroundColor Green
Write-Host "==========================================================" -ForegroundColor Green
