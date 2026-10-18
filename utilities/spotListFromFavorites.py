import requests
import re
import json
import os
import sys

BASE_URL = "https://www.surfline.com/"

# SF to Jetty map view, for further testing, not currently used
mapUrl = "https://www.surfline.com/surf-reports-forecasts-cams-map/@37.667516276171426,-122.41310119628908,11z"

COOKIES_FILE = "cookies.txt"

def load_cookies(filepath):
    """Loads cookies from a Netscape formatted cookies.txt file or simple name=value pairs."""
    cookies = {}
    if not os.path.exists(filepath):
        print(f"Warning: {filepath} not found. Request will be unauthenticated (likely 0 favorites).")
        return cookies

    try:
        with open(filepath, encoding="utf-8") as handle:
            for line in handle:
                if line.startswith('#') or not line.strip():
                    continue

                # Check for raw cookie header format (key=val; key2=val2)
                if ';' in line:
                    raw_cookies = line.split(';')
                    for cookie in raw_cookies:
                        if '=' in cookie:
                            key, val = cookie.strip().split('=', 1)
                            cookies[key.strip()] = val.strip()
                    continue

                # Simple Netscape/wget format parsing (tab separated)
                parts = line.strip().split('\t')
                if len(parts) >= 7:
                    cookies[parts[5]] = parts[6]
                elif '=' in line:  # Fallback for simple key=value lines
                    key, val = line.strip().split('=', 1)
                    cookies[key.strip()] = val.strip()
    except Exception as e:
        print(f"Error reading cookies: {e}")

    return cookies

def extract_favorites():
    cookies = load_cookies(COOKIES_FILE)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    try:
        print(f"Fetching {BASE_URL}...")
        response = requests.get(BASE_URL, headers=headers, cookies=cookies)
        response.raise_for_status()
        
        html_content = response.text
        
        print("Parsing HTML for __NEXT_DATA__...")
        # Regex to find the <script id="__NEXT_DATA__" ...>...</script> block
        match = re.search(r'<script id="__NEXT_DATA__" type="application/json"[^>]*>(.*?)</script>', html_content, re.DOTALL)
        
        if not match:
            print("Error: Could not find __NEXT_DATA__ script tag in response.")
            return

        json_str = match.group(1)
        data = json.loads(json_str)
        
        # Navigate to favorites
        # Path: props.pageProps.ssrReduxState.backplane.user.favorites
        try:
            user_data = data.get('props', {}).get('pageProps', {}).get('ssrReduxState', {}).get('backplane', {}).get('user', {})
            favorites = user_data.get('favorites', [])
            
            if not favorites:
                print("No favorites found. (Check your cookies/authentication)")
            else:
                print(f"Found {len(favorites)} favorites.")
                
                # Output formatted JSON to stdout
                output = json.dumps(favorites, indent=3)
                print("\n" + output)
                
                # Optionally save to file
                with open("favorites_list.json", "w") as f:
                    f.write(output)
                print("\nSaved to favorites_list.json")

        except AttributeError as e:
            print(f"Error navigating JSON structure: {e}")
            
    except requests.RequestException as e:
        print(f"HTTP Request failed: {e}")
    except json.JSONDecodeError as e:
        print(f"JSON Parsing failed: {e}")

if __name__ == "__main__":
    extract_favorites()
