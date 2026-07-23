import requests
import time
import logging
from datetime import datetime
import threading

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("keep_alive.log"),
        logging.StreamHandler()
    ]
)

# URL of your Koyeb app - replace with your actual app URL
APP_URL = "YOUR_KOYEB_APP_URL"  # User will need to replace this

# Ping interval in seconds (55 minutes = 3300 seconds)
# Setting to 55 minutes to ensure we ping before the 60-minute inactivity timeout
PING_INTERVAL = 3300

def ping_server():
    """Send a request to the server to keep it alive"""
    try:
        response = requests.get(APP_URL)
        logging.info(f"Ping sent at {datetime.now()} - Status code: {response.status_code}")
        return True
    except Exception as e:
        logging.error(f"Error pinging server: {e}")
        return False

def keep_alive_loop():
    """Run the keep-alive loop in a separate thread"""
    logging.info("Keep-alive thread started")
    
    while True:
        ping_result = ping_server()
        if ping_result:
            logging.info(f"Server pinged successfully. Sleeping for {PING_INTERVAL} seconds...")
        else:
            logging.warning(f"Failed to ping server. Will retry in {PING_INTERVAL} seconds...")
        
        # Sleep until next ping
        time.sleep(PING_INTERVAL)

def start_keep_alive_thread():
    """Start the keep-alive process in a background thread"""
    keep_alive_thread = threading.Thread(target=keep_alive_loop, daemon=True)
    keep_alive_thread.start()
    logging.info("Keep-alive thread started in background")
    return keep_alive_thread

# If running as standalone script
if __name__ == "__main__":
    logging.info("Keep-alive script started in standalone mode")
    keep_alive_loop()
        
