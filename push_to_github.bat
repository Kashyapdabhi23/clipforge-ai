@echo off
title Push ClipForge AI to GitHub
color 0b
echo ========================================================
echo   Pushing ClipForge AI to GitHub Repository:
echo   https://github.com/Kashyapdabhi23/clipforge-ai
echo ========================================================
echo.
cd /d D:\clipforge-ai
git push -u origin main
echo.
if %ERRORLEVEL% EQU 0 (
    echo ========================================================
    echo   [SUCCESS] Code successfully pushed to GitHub!
    echo   View your repository at:
    echo   https://github.com/Kashyapdabhi23/clipforge-ai
    echo ========================================================
) else (
    echo ========================================================
    echo   If prompted to Sign In, please click "Sign in with your browser"
    echo   or enter your GitHub Personal Access Token.
    echo ========================================================
)
echo.
pause
