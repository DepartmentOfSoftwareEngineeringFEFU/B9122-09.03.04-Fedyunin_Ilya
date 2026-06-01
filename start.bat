@echo off
title Запуск библиотечной системы ДВФУ
echo ========================================
echo   Научная библиотека ДВФУ
echo   Подсистема аннотирования и реферирования
echo ========================================
echo.

echo [1/2] Запуск бэкенда (FastAPI)...
start "Бэкенд ДВФУ" cmd /k "cd /d %~dp0 && venv\Scripts\activate && python main.py"

echo Ждём 3 секунды перед запуском фронтенда...
timeout /t 3 /nobreak >nul

echo [2/2] Запуск фронтенда (React)...
start "Фронтенд ДВФУ" cmd /k "cd /d %~dp0frontend && npm run dev"

echo.
echo ========================================
echo   Бэкенд: http://127.0.0.1:8000
echo   Фронтенд: http://localhost:5173
echo   Swagger UI: http://127.0.0.1:8000/docs
echo ========================================
echo.
echo Окна запущены. Не закрывайте их!
pause