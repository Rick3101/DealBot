Write-Host "===============================================" -ForegroundColor Cyan
Write-Host " Pirates Expedition Mini App Setup" -ForegroundColor Cyan
Write-Host "===============================================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/4] Installing webapp dependencies..." -ForegroundColor Yellow
Set-Location webapp
try {
    npm install
    if ($LASTEXITCODE -ne 0) { throw "npm install failed" }
    Write-Host "✅ Webapp dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to install webapp dependencies" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host ""
Write-Host "[2/4] Building Mini App..." -ForegroundColor Yellow
try {
    npm run build
    if ($LASTEXITCODE -ne 0) { throw "npm run build failed" }
    Write-Host "✅ Mini App built successfully" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to build Mini App" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host ""
Write-Host "[3/4] Installing bot dependencies..." -ForegroundColor Yellow
Set-Location ..
try {
    pip install -r requirements.txt
    if ($LASTEXITCODE -ne 0) { throw "pip install failed" }
    Write-Host "✅ Bot dependencies installed" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Failed to install bot dependencies" -ForegroundColor Red
    Read-Host "Press any key to exit"
    exit 1
}

Write-Host ""
Write-Host "[4/4] Setup complete!" -ForegroundColor Yellow
Write-Host ""
Write-Host "===============================================" -ForegroundColor Green
Write-Host " Mini App Setup Successful!" -ForegroundColor Green
Write-Host "===============================================" -ForegroundColor Green
Write-Host ""
Write-Host "🏴‍☠️ The Pirates Expedition Mini App is now ready!" -ForegroundColor Cyan
Write-Host ""
Write-Host "To start the bot with Mini App support:" -ForegroundColor White
Write-Host "  python app.py" -ForegroundColor Yellow
Write-Host ""
Write-Host "The Mini App will be available at:" -ForegroundColor White
Write-Host "  [YOUR_DOMAIN]/webapp" -ForegroundColor Yellow
Write-Host ""
Write-Host "Bot commands to access Mini App:" -ForegroundColor White
Write-Host "  /expedition" -ForegroundColor Yellow
Write-Host "  /dashboard" -ForegroundColor Yellow
Write-Host "  /miniapp" -ForegroundColor Yellow
Write-Host ""
Read-Host "Press any key to exit"