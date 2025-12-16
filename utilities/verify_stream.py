import requests

url = "https://hls.cdn-surfline.com/oregon/wc-wanderinnpacifica/playlist.m3u8"

print("Checking without Referer...")
try:
    r = requests.get(url)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")

print("\nChecking with Referer...")
try:
    headers = {"Referer": "https://www.surfline.com/"}
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
except Exception as e:
    print(f"Error: {e}")
