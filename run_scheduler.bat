@echo off
title Telecom Outage Scheduler
cd /d "d:\94 FAH works\Telecom-Outage"
set PYTHONPATH=d:\94 FAH works\Telecom-Outage

if not exist logs mkdir logs

echo [%date% %time%] Starting Telecom Outage Scheduler... >> logs\scraper.log

:loop
echo [%date% %time%] Running scraper... >> logs\scraper.log
python -m scrapers.run >> logs\scraper.log 2>&1
echo [%date% %time%] Done. Waiting 5 minutes... >> logs\scraper.log
timeout /t 300 /nobreak >nul
goto loop
