@echo off
echo ===============================================
echo  Pirates Expedition Mini App Setup
echo ===============================================
echo.

echo [1/4] Installing webapp dependencies...
cd webapp
if not exist "package.json" (
    echo ERROR: package.json not found in webapp directory
    cd ..
    pause
    exit /b 1
)

call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install webapp dependencies
    echo Exit code: %errorlevel%
    cd ..
    pause
    exit /b 1
)

echo.
echo [2/4] Building Mini App...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Failed to build Mini App
    echo Exit code: %errorlevel%
    echo.
    echo Build output saved. Check for TypeScript errors above.
    cd ..
    pause
    exit /b 1
)

echo.
echo [3/4] Installing bot dependencies...
cd ..
if not exist "requirements.txt" (
    echo ERROR: requirements.txt not found
    pause
    exit /b 1
)

pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install bot dependencies
    echo Exit code: %errorlevel%
    pause
    exit /b 1
)

echo.
echo [4/4] Setup complete!
echo.
echo ===============================================
echo  Mini App Setup Successful!
echo ===============================================
echo.
echo Build artifacts:
dir /b webapp\dist 2>nul
if %errorlevel% neq 0 (
    echo WARNING: dist folder not found
) else (
    echo   Dist folder created successfully
)
echo.
echo The Pirates Expedition Mini App is now ready!
echo.
echo To start the bot with Mini App support:
echo   python app.py
echo.
echo The Mini App will be available at:
echo   http://localhost:5000/webapp
echo.
echo Bot commands to access Mini App:
echo   /expedition
echo   /dashboard
echo   /miniapp
echo.
echo ===============================================
echo Setup completed successfully at %date% %time%
echo ===============================================
pause
