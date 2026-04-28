@echo off
echo Starting Telecom Outage Backend...
cd /d "%~dp0"
set PYTHONPATH=.
python -m uvicorn backend.main:app --host 0.0.0.0 --port 8080 --reload
pause
