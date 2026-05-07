@echo off
echo ========================================
echo   DealSathi GitHub Upload Assistant
echo ========================================

:: Check if git is initialized
if not exist .git (
    echo Initializing Git repository...
    git init
)

:: Add all files
echo Adding files...
git add .

:: Initial commit
echo Creating initial commit...
git commit -m "Deployment ready: Sasto Bazar Dashboard"

:: Set Branch and Remote
echo Setting up branch and remote...
git branch -M main
git remote remove origin >nul 2>&1
git remote add origin https://github.com/ghanshyamoli9745-bot/sasto-bazar.git

echo.
echo ========================================
echo   PUSHING TO GITHUB...
echo ========================================
echo Running: git push -u origin main
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo [SUCCESS] Code pushed to GitHub!
    echo Render will now start building automatically.
) else (
    echo.
    echo [ERROR] Push failed. Please check if you are logged into Git.
    echo You might need to run: git push -u origin main manually.
)

echo.
echo ========================================
pause
