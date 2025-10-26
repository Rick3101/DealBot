@echo off
echo ===============================================
echo  Pirates Expedition Mini App Setup
echo ===============================================
echo.

echo [1/4] Installing webapp dependencies...
cd webapp
call npm install
if %errorlevel% neq 0 (
    echo ERROR: Failed to install webapp dependencies
    pause
    exit /b 1
)

echo.
echo [2/4] Building Mini App...
call npm run build
if %errorlevel% neq 0 (
    echo ERROR: Failed to build Mini App
    pause
    exit /b 1
)

echo.
echo [3/4] Installing bot dependencies...
cd ..
pip install -r requirements.txt
if %errorlevel% neq 0 (
    echo ERROR: Failed to install bot dependencies
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
echo The Pirates Expedition Mini App is now ready!
echo.
echo To start the bot with Mini App support:
echo   python app.py
echo.
echo The Mini App will be available at:
echo   [YOUR_DOMAIN]/webapp
echo.
echo Bot commands to access Mini App:
echo   /expedition
echo   /dashboard
echo   /miniapp
echo.
pause