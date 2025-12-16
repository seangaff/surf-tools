import requests

url = "https://hls.cdn-surfline.com/oregon/wc-wanderinnpacifica/playlist.m3u8"
iphone_ua = "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"

print("--- Test 1: No Referer, Standard UA ---")
try:
    r = requests.get(url)
    print(f"Status: {r.status_code}")
except Exception as e: print(e)

print("\n--- Test 2: No Referer, iPhone UA ---")
try:
    headers = {"User-Agent": iphone_ua}
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
except Exception as e: print(e)

print("\n--- Test 3: Origin 'null' (Local file simulation) ---")
try:
    headers = {"Origin": "null", "Referer": "null"}
    r = requests.get(url, headers=headers)
    print(f"Status: {r.status_code}")
except Exception as e: print(e)
