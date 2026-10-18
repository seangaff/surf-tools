#!/usr/bin/env python3
"""Collect Surfline cam streams for a region.

Favorites and a saved HTML dump only see spots already on your account.
Surfline's public APIs cover a whole place in two calls:

1. Taxonomy lists every spot filed under a geoname (San Diego county is
   5391832, including San Onofre and Trestles).
2. Mapview returns those spots, with HLS stream URLs, for a bounding box.

The script joins them. Neighbors that merely fall inside the box, such as
San Clemente, are left out. Spots the map call misses are filled in from
the per-spot report endpoint.

    python utilities/collect_region_cams.py san-diego
"""

import argparse
import json
import sys
import time
from pathlib import Path

try:
    from curl_cffi import requests
except ImportError:
    sys.exit("curl_cffi is required (Cloudflare blocks urllib/requests). pip install curl_cffi")

ROOT = Path(__file__).resolve().parents[1]
API = "https://services.surfline.com"

# Coastal box around San Diego county, padded into San Onofre.
# Taxonomy decides which of these spots count as San Diego.
PRESETS = {
    "san-diego": {
        "name": "San Diego",
        "geoname_id": 5391832,
        "south": 32.50,
        "west": -117.70,
        "north": 33.50,
        "east": -117.00,
        "output": ROOT / "data" / "sanDiegoSpotData.json",
    }
}

CAMERA_FIELDS = (
    "_id",
    "title",
    "streamUrl",
    "stillUrlFull",
    "rewindBaseUrl",
    "alias",
    "isPremium",
)


def get_json(path, params):
    response = requests.get(
        f"{API}{path}",
        params=params,
        impersonate="chrome",
        timeout=30,
    )
    response.raise_for_status()
    return response.json()


def spot_id_from_entry(entry):
    for link in entry.get("associated", {}).get("links") or []:
        if not link:
            continue
        href = link.get("href") or ""
        if link.get("key") == "api" and "/spots/" in href:
            return href.rstrip("/").split("/")[-1]
    return None


def collect_spot_ids(geoname_id):
    """Spot ids Surfline files under this geoname, including child places."""
    spot_ids = []
    seen = set()
    pending = [geoname_id]
    visited = set()

    while pending:
        geoname_id = pending.pop(0)
        if geoname_id in visited:
            continue
        visited.add(geoname_id)
        payload = get_json("/taxonomy", {"type": "geoname", "id": geoname_id, "maxDepth": 1})
        for entry in payload.get("contains") or []:
            if entry.get("type") == "spot":
                spot_id = spot_id_from_entry(entry)
                if spot_id and spot_id not in seen:
                    seen.add(spot_id)
                    spot_ids.append(spot_id)
            elif entry.get("type") == "geoname":
                child_id = None
                for link in entry.get("associated", {}).get("links") or []:
                    if link and link.get("key") == "taxonomy":
                        # .../taxonomy?id=5396974&type=geoname
                        query = link["href"].split("?", 1)[-1]
                        for part in query.split("&"):
                            if part.startswith("id="):
                                child_id = part.split("=", 1)[1]
                if child_id:
                    pending.append(child_id)
        time.sleep(0.15)

    return spot_ids


def map_spots(south, west, north, east):
    payload = get_json(
        "/kbyg/mapview",
        {"south": south, "west": west, "north": north, "east": east},
    )
    return payload.get("data", {}).get("spots") or []


def report_spot(spot_id):
    payload = get_json("/kbyg/spots/reports", {"spotId": spot_id})
    return payload.get("spot") or {}


def slim_camera(camera):
    slim = {field: camera.get(field) for field in CAMERA_FIELDS}
    status = camera.get("status") or {}
    slim["isDown"] = bool(status.get("isDown"))
    return slim


def slim_spot(spot):
    subregion = spot.get("subregion") or {}
    cameras = [slim_camera(cam) for cam in spot.get("cameras") or [] if cam.get("streamUrl")]
    return {
        "_id": spot.get("_id"),
        "lat": spot.get("lat"),
        "lon": spot.get("lon"),
        "name": spot.get("name"),
        "subregionId": subregion.get("_id") or spot.get("subregionId"),
        "subregionName": subregion.get("name") or spot.get("subregionName"),
        "cameras": cameras,
    }


def build(preset, cams_only):
    print(f"Listing spots in {preset['name']} ({preset['geoname_id']})...")
    spot_ids = collect_spot_ids(preset["geoname_id"])
    print(f"Taxonomy returned {len(spot_ids)} spots.")

    print("Fetching cameras from mapview...")
    by_id = {spot["_id"]: spot for spot in map_spots(
        preset["south"], preset["west"], preset["north"], preset["east"]
    )}

    missing = [spot_id for spot_id in spot_ids if spot_id not in by_id]
    if missing:
        print(f"{len(missing)} spots were outside the map box; fetching reports...")
        for spot_id in missing:
            spot = report_spot(spot_id)
            if spot:
                by_id[spot_id] = spot
            time.sleep(0.15)

    ordered = []
    absent = []
    for spot_id in spot_ids:
        spot = by_id.get(spot_id)
        if not spot:
            absent.append(spot_id)
            continue
        ordered.append(slim_spot(spot))

    if absent:
        print(f"Warning: no details for {len(absent)} spots: {', '.join(absent)}")

    skipped = [spot["name"] for spot in ordered if not spot["cameras"]]
    if cams_only:
        ordered = [spot for spot in ordered if spot["cameras"]]

    ordered.sort(key=lambda spot: -(spot["lat"] or 0))

    cam_count = sum(len(spot["cameras"]) for spot in ordered)
    print(f"{len(ordered)} spots, {cam_count} streams.")
    if skipped:
        print(f"Skipped {len(skipped)} spots with no stream: {', '.join(skipped)}")

    outside = sorted(
        spot["name"]
        for spot in by_id.values()
        if spot.get("_id") not in set(spot_ids)
    )
    if outside:
        print(f"Left out {len(outside)} map spots that are not in this region: {', '.join(outside)}")

    return {
        "region": preset["name"],
        "geonameId": preset["geoname_id"],
        "spots": ordered,
    }


def main():
    parser = argparse.ArgumentParser(description="Collect Surfline cam streams for a region.")
    parser.add_argument("preset", choices=sorted(PRESETS), help="Named region to collect")
    parser.add_argument(
        "--include-empty",
        action="store_true",
        help="Keep spots that have no camera stream",
    )
    parser.add_argument("-o", "--output", type=Path, help="Override the output JSON path")
    args = parser.parse_args()

    preset = dict(PRESETS[args.preset])
    if args.output:
        preset["output"] = args.output

    catalog = build(preset, cams_only=not args.include_empty)
    output = Path(preset["output"])
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(catalog, indent=4) + "\n", encoding="utf-8")
    print(f"Wrote {output}")


if __name__ == "__main__":
    main()
