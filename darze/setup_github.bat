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
git commit -m "Initial release: Premium DealSathi Dashboard"

echo.
echo ========================================
echo   NEXT STEPS:
echo ========================================
echo 1. Go to https://github.com/new
echo 2. Create a repository named "dealsathi"
echo 3. Run the following commands:
echo.
echo    git branch -M main
echo    git remote add origin https://github.com/YOUR_USERNAME/dealsathi.git
echo    git push -u origin main
echo.
echo ========================================
pause
