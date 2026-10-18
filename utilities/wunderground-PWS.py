from bs4 import BeautifulSoup
import json
import re
import requests

#  Weather Underground Personal Weather Station(PWS), get data accurate to specific spot.

PWS_ID = "KCAPACIF185"
PWS_API_URL_PATTERN = re.compile(
    r"https://api\.weather\.com/v2/pws/observations/all/1day\?[^\"']+"
)


def fetch_wunderground_pws(pws_id):
    url = f"https://www.wunderground.com/dashboard/pws/{pws_id}"
    response = requests.get(url)
    html = response.text
    return html, BeautifulSoup(html, "html.parser")


def get_wunderground_PWS(pws_id):
    _, soup = fetch_wunderground_pws(pws_id)
    return soup


def _parse_number(value):
    if value is None:
        return None
    try:
        return int(value) if value.isdigit() else float(value)
    except (ValueError, AttributeError):
        return value


def _parse_display_unit(element):
    if element is None:
        return None

    no_value = element.find(class_="wu-unit-no-value")
    if no_value:
        raw = no_value.get_text(strip=True)
        return {"value": None, "unit": None, "raw": raw}

    value_el = element.find(class_="wu-value-to") or element.find(class_="wu-value")
    if value_el is None:
        return None

    label = element.find(class_="wu-label")
    unit = ""
    if label:
        unit = "".join(text for text in label.stripped_strings if text != "°")

    value = value_el.get_text(strip=True)
    return {
        "value": _parse_number(value),
        "unit": unit or None,
    }


def _header_to_key(header):
    return header.strip().lower().replace(" ", "_").replace("&", "and")


def _degrees_to_compass(degrees):
    if degrees is None:
        return None
    directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    index = round(float(degrees) / 22.5) % len(directions)
    return directions[index]


def _metric(value, unit):
    if value is None:
        return {"value": None, "unit": unit}
    return {"value": value, "unit": unit}


def _normalize_observation(obs, source):
    imperial = obs.get("imperial", {})
    is_current = "temp" in imperial

    if is_current:
        temp = imperial.get("temp")
        feels_like = imperial.get("heatIndex")
        wind_speed = imperial.get("windSpeed")
        wind_gust = imperial.get("windGust")
        dewpoint = imperial.get("dewpt")
        pressure = imperial.get("pressure")
        precip_rate = imperial.get("precipRate")
        precip_total = imperial.get("precipTotal")
        wind_degrees = obs.get("winddir")
        humidity = obs.get("humidity")
        uv = obs.get("uv")
    else:
        temp = imperial.get("tempAvg")
        feels_like = imperial.get("heatindexAvg")
        wind_speed = imperial.get("windspeedAvg")
        wind_gust = imperial.get("windgustAvg")
        dewpoint = imperial.get("dewptAvg")
        pressure = imperial.get("pressureMax")
        precip_rate = imperial.get("precipRate")
        precip_total = imperial.get("precipTotal")
        wind_degrees = obs.get("winddirAvg")
        humidity = obs.get("humidityAvg")
        uv = obs.get("uvHigh")

    return {
        "source": source,
        "station_id": obs.get("stationID"),
        "obs_time_utc": obs.get("obsTimeUtc"),
        "obs_time_local": obs.get("obsTimeLocal"),
        "temperature": _metric(temp, "F"),
        "feels_like": _metric(feels_like, "F"),
        "wind_direction": {
            "degrees": wind_degrees,
            "compass": _degrees_to_compass(wind_degrees),
        },
        "wind": _metric(wind_speed, "mph"),
        "gust": _metric(wind_gust, "mph"),
        "dewpoint": _metric(dewpoint, "F"),
        "precip_rate": _metric(precip_rate, "in/hr"),
        "pressure": _metric(pressure, "in"),
        "humidity": _metric(humidity, "%"),
        "precip_accum": _metric(precip_total, "in"),
        "uv": _metric(uv, None),
    }


def extract_pws_api_url(html, pws_id):
    match = PWS_API_URL_PATTERN.search(html)
    if match is None:
        return None

    api_url = match.group(0)
    if f"stationId={pws_id}" not in api_url:
        api_url = re.sub(r"stationId=[^&]+", f"stationId={pws_id}", api_url)

    return api_url.replace("observations/all/1day", "observations/current")


def get_live_conditions_from_api(page, pws_id=PWS_ID):
    html = page if isinstance(page, str) else str(page)
    api_url = extract_pws_api_url(html, pws_id)
    if api_url is None:
        return None

    response = requests.get(api_url)
    response.raise_for_status()
    observations = response.json().get("observations", [])
    if not observations:
        return None

    conditions = _normalize_observation(observations[0], "api")
    conditions["api_url"] = api_url.split("apiKey=")[0] + "apiKey=..."
    return conditions


def _find_embedded_observations(soup, pws_id):
    observations = []
    for script in soup.find_all("script", type="application/json"):
        if not script.string:
            continue
        try:
            payload = json.loads(script.string)
        except json.JSONDecodeError:
            continue

        for entry in payload.values():
            if not isinstance(entry, dict):
                continue
            body = entry.get("b")
            if not isinstance(body, dict):
                continue
            obs_list = body.get("observations")
            if not isinstance(obs_list, list):
                continue
            observations.extend(
                obs
                for obs in obs_list
                if isinstance(obs, dict) and obs.get("stationID") == pws_id
            )

    if not observations:
        return None

    return max(observations, key=lambda obs: obs.get("epoch", 0))


def get_live_conditions_from_embedded_json(soup, pws_id=PWS_ID):
    observation = _find_embedded_observations(soup, pws_id)
    if observation is None:
        return None

    return _normalize_observation(observation, "embedded_json")




if __name__ == "__main__":
    print(f"\nLive PWS {PWS_ID}:")
    html, soup = fetch_wunderground_pws(PWS_ID)

    print("\nOption 2 - scrape API URL from page, fetch current obs:")
    api_conditions = get_live_conditions_from_api(html, PWS_ID)
    print(json.dumps(api_conditions, indent=2))

    print("\nOption 3 - parse embedded JSON, latest 5-min observation:")
    embedded_conditions = get_live_conditions_from_embedded_json(soup, PWS_ID)
    print(json.dumps(embedded_conditions, indent=2))
