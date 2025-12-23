import requests
import time
import os
from datetime import datetime

URL = "https://camstills.cdn-surfline.com/us-west-2/wc-tacobellpacifica/latest_full.jpg"
DOWNLOAD_DIR = "stills"
INTERVAL_SECONDS = 600  # 10 minutes

def download_image():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    while True:
        try:
            response = requests.get(URL)
            response.raise_for_status()
            
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            filename = f"surf_still_{timestamp}.jpg"
            filepath = os.path.join(DOWNLOAD_DIR, filename)

            with open(filepath, "wb") as f:
                f.write(response.content)
            
            print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloaded {filename}")
            
        except Exception as e:
            print(f"Error downloading image: {e}")

        time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    print(f"Starting periodic download from {URL}")
    print(f"Saving to {DOWNLOAD_DIR}/ every {INTERVAL_SECONDS} seconds.")
    download_image()