@echo off
echo ========================================================
echo        Starting ClipForge AI - Frontend Dashboard
echo ========================================================
cd /d %~dp0\frontend
call npm.cmd run dev
pause
