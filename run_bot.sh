#!/bin/bash

# This script sets up and runs the FileStore bot with the keep-alive mechanism
# to prevent Koyeb instance from sleeping

# Check if APP_URL is provided
if [ -z "$1" ]; then
  echo "Error: Koyeb app URL not provided"
  echo "Usage: ./run_bot.sh YOUR_KOYEB_APP_URL"
  exit 1
fi

# Set the APP_URL in keep_alive.py
APP_URL=$1
echo "Setting Koyeb app URL to: $APP_URL"
sed -i "s|APP_URL = \"YOUR_KOYEB_APP_URL\"|APP_URL = \"$APP_URL\"|g" keep_alive.py

# Install required dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Add requests to requirements if not already there
if ! grep -q "requests" requirements.txt; then
  echo "Adding requests to requirements.txt..."
  echo "requests" >> requirements.txt
  pip install requests
fi

# Start the bot
echo "Starting FileStore bot with keep-alive mechanism..."
python3 main.py
