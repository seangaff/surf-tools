import json
import requests


testURL = "https://services.surfline.com/kbyg/spots/forecasts/wave?spotId=5842041f4e65fad6a7708976&days=1&intervalHours=1"


def get_json_url(url):
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return response.status_code


data = get_json_url(testURL)

# print(data["associated"])
# print(len(data))
# print(data["data"].keys())
count = 0
for x in data["data"]["wave"]:
    print(json.dumps(x, indent=4))
    # print(x['timestamp'])
    count +=1 
    