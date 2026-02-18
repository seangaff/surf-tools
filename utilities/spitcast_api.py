# https://github.com/jackmullis/spitcast-api-docs
# Spot data in data/spitcast_spot.json last updated 1/30/26

# Endpoint Format:
# https://api.spitcast.com/api/spot_forecast/{spot_id}/{year}/{month}/{day}

# Example:
# https://api.spitcast.com/api/spot_forecast/1/2025/3/14

import requests
import json
import datetime

# Returns current date in format: YYYY/MM/DD
# WITHOUT 0 padding for month and day
def get_current_date():
    return datetime.datetime.now().strftime("%Y/%-m/%-d")



def get_spot_forecast(spot_id, strf_date):
    url = f"https://api.spitcast.com/api/spot_forecast/{spot_id}/{strf_date}"
    print(url)
    try:
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching spot forecast: {e}")
        return None
    


if __name__ == "__main__":
    spot_id = 1
    print(json.dumps(get_spot_forecast(spot_id, get_current_date()), indent=4))
    # get_spot_forecast(spot_id, get_current_date())
    # print(type(get_current_date()))
