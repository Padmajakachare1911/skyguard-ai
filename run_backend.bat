@echo off
title SkyGuard AI - Backend Server (FastAPI)
color 0B
cls
echo ===================================================================
echo             SKYGUARD AI - FASTAPI BACKEND SERVER
echo ===================================================================
echo.
echo  Starting backend on all interfaces (0.0.0.0:8000)...
echo  Local access    : http://127.0.0.1:8000
echo  LAN/Wi-Fi access : http://192.168.1.6:8000
echo  API Documentation: http://127.0.0.1:8000/docs
echo.
echo ===================================================================
echo.

if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
) else if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
) else (
    python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
)

pause
