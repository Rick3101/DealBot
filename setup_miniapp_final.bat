@echo off
echo ===============================================
echo  Pirates Expedition Mini App Setup
echo ===============================================
echo.
echo This script will:
echo  1. Install webapp dependencies
echo  2. Build the Mini App for production
echo  3. Install Python bot dependencies
echo.
echo Press any key to continue or Ctrl+C to cancel...
pause > nul
echo.

echo [1/3] Installing webapp dependencies...
echo.
cd webapp
if not exist "package.json" (
    echo ERROR: package.json not found in webapp directory
    cd ..
    pause
    exit /b 1
)

call npm install
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install webapp dependencies
    echo Exit code: %errorlevel%
    echo.
    echo Try running: cd webapp ^&^& npm install --legacy-peer-deps
    cd ..
    pause
    exit /b 1
)

echo.
echo [2/3] Building Mini App for production...
echo.
call npm run build
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to build Mini App
    echo Exit code: %errorlevel%
    echo.
    echo Check the error messages above for details.
    echo Common issues:
    echo  - TypeScript errors: Fix type issues in source files
    echo  - Missing dependencies: Run npm install again
    cd ..
    pause
    exit /b 1
)

echo.
echo [3/3] Installing Python bot dependencies...
echo.
cd ..
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo.
    echo ERROR: Failed to install Python dependencies
    echo Exit code: %errorlevel%
    echo.
    echo Make sure you have Python and pip installed.
    pause
    exit /b 1
)

echo.
echo ===============================================
echo  Setup Complete!
echo ===============================================
echo.
echo Build artifacts created:
dir /b webapp\dist 2>nul | findstr /r ".*"
if %errorlevel% neq 0 (
    echo WARNING: dist folder not found
) else (
    echo.
    echo   Build successful - dist folder contains:
    echo   - index.html
    echo   - JavaScript bundles (gzipped)
    echo   - PWA service worker
    echo   - Assets and manifest
)

echo.
echo ===============================================
echo  Ready to Launch!
echo ===============================================
echo.
echo To start the Pirates Expedition Bot with Mini App:
echo   python app.py
echo.
echo The Mini App will be served at:
echo   http://localhost:5000/webapp/
echo.
echo Bot commands to access the Mini App:
echo   /expedition - Open expedition management
echo   /dashboard  - View dashboard
echo   /miniapp    - Launch full Mini App
echo.
echo ===============================================
echo Note: Storybook was removed from dependencies due
echo to version conflicts. The production build works
echo perfectly without it. You can add Storybook back
echo later if needed for component development.
echo ===============================================
echo.
pause
