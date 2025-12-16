from bs4 import BeautifulSoup
import json
import os
import re


with open('base.html', 'r', encoding='utf-8') as f:
    html = f.read()

soup = BeautifulSoup(html, 'html.parser')
for script in soup.find_all('script'):
    if script.string and '__USER_REDUX__' in script.string:
        match = re.search(r'window\.__USER_REDUX__\s*=\s*({.*?});', script.string, re.DOTALL)
        if match:
            data = json.loads(match.group(1))
            break


with open('userData.json', 'w') as f:
    f.write(json.dumps(data, indent=4))

favorites = data['favorites']


schema = {
    "favorites": [{
        "_id": True,
        "lat": True,
        "lon": True,
        "name": True,
        "subRegionID": True,
        "subregionName": True,
        "cameras": [{
            "_id": True,
            "title": True,
            "streamUrl": True,
            "stillUrlFull": True,
            "rewindBaseUrl": True,
            "alias": True
        }]
    }]
}

def filter_dict(data, schema):
    if isinstance(schema, dict):
        result = {}
        for key, value in schema.items():
            if key in data:
                if isinstance(value, dict):
                    result[key] = filter_dict(data[key], value)
                elif isinstance(value, list) and len(value) == 1:
                    result[key] = [filter_dict(item, value[0]) for item in data.get(key, [])]
                elif value is True:
                    result[key] = data[key]
        return result
    return data



filtered = filter_dict(data, schema)

print(json.dumps(filtered, indent=4))

with open('filteredSpotData.json', 'w') as f:
    f.write(json.dumps(filtered, indent=4))