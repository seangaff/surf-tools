# For all Linda Mar Cams, download stills every 10 minutes during daylight hours
# Create training data for person(surfer) counting

# Run continouesly
# Each day check first light and last light
# Download stills every 10 minzs between
# First iteration: Download stills between 7am-6pm(adjust in future)

import requests
import time
import os
from datetime import datetime
import json

DOWNLOAD_DIR = "../stills"
INTERVAL_SECONDS = 600  # 10 minutes
SPOT_DATA= "../data/filteredSpotData.json"
SUBREGION = "Pacifica"

# Daylight hours hardcoded
FIRST_LIGHT = 7
LAST_LIGHT = 18

cam_urls = []

def get_spot_list():
    with open(SPOT_DATA, "r") as f:
        data = json.load(f)

    for spot in data["favorites"]:
        if spot["subregionName"] == SUBREGION:
            for cam in spot["cameras"]:
                cam_urls.append([cam["alias"],cam["stillUrlFull"]])

# Is current time between first and last light
# First iteration hardcoded
def is_daylight():
    now = datetime.now()
    if now.hour >= FIRST_LIGHT and now.hour < LAST_LIGHT:
        return True
    return False

# Create directories for each cam
def create_dir():
    if not os.path.exists(DOWNLOAD_DIR):
        os.makedirs(DOWNLOAD_DIR)

    for cam in cam_urls:
        cam_dir = os.path.join(DOWNLOAD_DIR, cam[0])
        if not os.path.exists(cam_dir):
            os.makedirs(cam_dir)

def download_image(camData):
    alias = camData[0]
    url = camData[1]

    try:
        response = requests.get(url)
        response.raise_for_status()
        
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"{alias}_{timestamp}.jpg"
        filepath = os.path.join(DOWNLOAD_DIR, alias, filename)

        with open(filepath, "wb") as f:
            f.write(response.content)
        
        print(f"[{datetime.now().strftime('%H:%M:%S')}] Downloaded {filename}")
        
    except Exception as e:
        print(f"Error downloading image: {e}")

        

def download_loop():
    if is_daylight():
        for cam in cam_urls:
            download_image(cam)
    else:
        print("Not daylight, skipping download")

    time.sleep(INTERVAL_SECONDS)

if __name__ == "__main__":
    print(f"Starting periodic download for {SUBREGION}")
    print(f"Saving to {DOWNLOAD_DIR}/ every {int(INTERVAL_SECONDS/60)} minutes.")
    get_spot_list()
    create_dir()
    download_loop()
    


    # download_image()