@echo off
echo Starting Telecom Outage Frontend...
cd /d "%~dp0\frontend"
set NEXT_PUBLIC_API_URL=http://localhost:8080
call npm run dev
pause
