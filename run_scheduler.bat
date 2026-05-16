@echo off
title Telecom Outage - Full Stack
cd /d "d:\94 FAH works\Telecom-Outage"
set PYTHONPATH=d:\94 FAH works\Telecom-Outage
set PYTHONUTF8=1
chcp 65001 >nul

if not exist logs mkdir logs

echo [%date% %time%] Starting backend API server... >> logs\scheduler.log

:: Start FastAPI backend in a new window
start "Telecom API" cmd /k ".venv\Scripts\python.exe -m uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload"

:: Wait for backend to be ready
timeout /t 3 /nobreak >nul

echo [%date% %time%] Starting scraper loop... >> logs\scheduler.log

:loop
echo [%date% %time%] Running scraper... >> logs\scheduler.log
.venv\Scripts\python.exe -m scrapers.run >> logs\scheduler.log 2>&1
echo [%date% %time%] Done. Waiting 5 minutes... >> logs\scheduler.log
timeout /t 300 /nobreak >nul
goto loop
