#!/bin/bash

echo "==============================================="
echo " Pirates Expedition Mini App Setup"
echo "==============================================="
echo

echo "[1/4] Installing webapp dependencies..."
cd webapp
npm install
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install webapp dependencies"
    exit 1
fi

echo
echo "[2/4] Building Mini App..."
npm run build
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to build Mini App"
    exit 1
fi

echo
echo "[3/4] Installing bot dependencies..."
cd ..
pip install -r requirements.txt
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install bot dependencies"
    exit 1
fi

echo
echo "[4/4] Setup complete!"
echo
echo "==============================================="
echo " Mini App Setup Successful!"
echo "==============================================="
echo
echo "The Pirates Expedition Mini App is now ready!"
echo
echo "To start the bot with Mini App support:"
echo "  python app.py"
echo
echo "The Mini App will be available at:"
echo "  [YOUR_DOMAIN]/webapp"
echo
echo "Bot commands to access Mini App:"
echo "  /expedition"
echo "  /dashboard"
echo "  /miniapp"
echo