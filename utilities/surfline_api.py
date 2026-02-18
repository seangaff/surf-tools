# https://services.surfline.com/kbyg/spots/forecasts/{type}?{params}

# Linda Mar 6 days at 1 hour
# https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708976&days=6&intervalHours=1&maxHeights=false

import requests
import json


# Returns json
def get_surfline_forecast(spot_id, forecast_type='wave', days=6, interval_hours=1, max_heights=False):
    url = f'https://services.surfline.com/kbyg/spots/forecasts/{forecast_type}?spotId={spot_id}&days={days}&intervalHours={interval_hours}&maxHeights={str(max_heights).lower()}'
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Error fetching data from Surfline API: {response.status_code} - {response.text}")
    

def extract_wave_data(forecast: json) -> list:
    wave_data = []
    for entry in forecast.get('data', []):
        timestamp = entry.get('timestamp')
        height = entry.get('surf', {}).get('min')
        period = entry.get('surf', {}).get('period')
        direction = entry.get('surf', {}).get('direction')
        wave_data.append({
            'timestamp': timestamp,
            'height': height,
            'period': period,
            'direction': direction
        })
    return wave_data

if __name__ == "__main__":
    spot_id = '5842041f4e65fad6a7708976'  # Linda Mar
    forecast = get_surfline_forecast(spot_id, days=1)
    print(len(forecast["data"]["wave"]))
    # print(json.dumps(forecast, indent=2))