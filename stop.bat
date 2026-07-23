@echo off
REM ============================================================
REM  T2SQL - servisleri durdur (Backend + Frontend)
REM  Postgres (Docker) acik kalir; verilerin kaybolmaz.
REM  Postgres'i de durdurmak istersen en alttaki satiri ac.
REM ============================================================

echo Backend (port 8000) durduruluyor...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

echo Frontend (port 3000) durduruluyor...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :3000 ^| findstr LISTENING') do taskkill /PID %%a /F >nul 2>&1

REM Postgres'i de durdurmak icin asagidaki satirin basindaki REM'i kaldir:
REM docker compose down

echo.
echo Backend ve frontend durduruldu. (Postgres calismaya devam ediyor)
echo.
pause
