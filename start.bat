@echo off
REM ============================================================
REM  T2SQL - tum servisleri baslat (Postgres + Backend + Frontend)
REM  Cift tikla veya terminalden: start.bat
REM ============================================================
cd /d "%~dp0"

echo [1/3] PostgreSQL (Docker) baslatiliyor...
docker compose up -d
if errorlevel 1 (
    echo    ! Docker baslatilamadi. Docker Desktop calisiyor mu?
    echo    ! Postgres olmadan backend calismaz.
)

echo [2/3] Backend (FastAPI) baslatiliyor - yeni pencere...
start "T2SQL Backend" cmd /k "cd /d %~dp0backend && call .venv\Scripts\activate.bat && uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload"

echo [3/3] Frontend (Next.js) baslatiliyor - yeni pencere...
start "T2SQL Frontend" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ============================================================
echo  Servisler baslatildi:
echo    Backend  : http://127.0.0.1:8000/api/health
echo    Frontend : http://localhost:3000
echo.
echo  Durdurmak icin: stop.bat
echo ============================================================
echo.
pause
