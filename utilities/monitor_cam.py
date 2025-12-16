import requests
import time
from datetime import datetime
from email.utils import parsedate_to_datetime

URL = "https://camstills.cdn-surfline.com/us-west-2/wc-tacobellpacifica/latest_full.jpg"
POLL_INTERVAL = 60  # Check every 10 seconds

def get_last_modified(url):
    try:
        response = requests.head(url)
        response.raise_for_status()
        last_modified_str = response.headers.get('Last-Modified')
        if last_modified_str:
            return parsedate_to_datetime(last_modified_str)
    except requests.RequestException as e:
        print(f"Error checking URL: {e}")
    return None

def main():
    print(f"Monitoring {URL}...")
    print("Press Ctrl+C to stop.")

    last_update_time = get_last_modified(URL)
    if last_update_time:
        print(f"Initial Last-Modified: {last_update_time}")
    else:
        print("Could not get initial Last-Modified timestamp.")
        # Proceed anyway, next successful check will set it

    while True:
        try:
            current_update_time = get_last_modified(URL)

            if current_update_time and current_update_time != last_update_time:
                now = datetime.now()
                print(f"[{now.strftime('%H:%M:%S')}] Image updated! New Last-Modified: {current_update_time}")
                
                if last_update_time:
                    interval = current_update_time - last_update_time
                    print(f"  Time since previous update: {interval}")
                
                last_update_time = current_update_time
            
            time.sleep(POLL_INTERVAL)

        except KeyboardInterrupt:
            print("\nMonitoring stopped.")
            break
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            time.sleep(POLL_INTERVAL)

if __name__ == "__main__":
    main()
