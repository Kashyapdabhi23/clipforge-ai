@echo off
echo ========================================================
echo               Launching ClipForge AI
echo ========================================================
echo Starting Backend API Server (Port 8000)...
start "ClipForge AI - Backend" cmd /c "cd /d %~dp0 && run_backend.bat"

timeout /t 3 /nobreak >nul

echo Starting Frontend Dev Server (Port 5173)...
start "ClipForge AI - Frontend" cmd /c "cd /d %~dp0 && run_frontend.bat"

timeout /t 3 /nobreak >nul
echo.
echo ========================================================
echo ClipForge AI is running!
echo Open your browser at: http://localhost:5173
echo ========================================================
pause
