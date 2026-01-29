import urllib.parse
from pathlib import Path

import requests

from ..common import Icon, Map, Place, dump, get_fair_user_agent, get_update_date, image_url_to_dataurl, load

NAME = "Jerusalem"
JSON_NAME = "jerusalem_shelters.json"
BASE_URL = "https://www.jerusalem.muni.il/umbraco/api/map/GetMapById"


def generate_map(data_dir: Path, icons_as_dataurls: bool = True):
    json_path = data_dir / JSON_NAME
    data = load(json_path)
    update_date = get_update_date(json_path)

    icons = []
    places = []
    seen = set()

    for group in data:
        url = urllib.parse.urljoin(BASE_URL, group["Icon"])
        if icons_as_dataurls:
            url = image_url_to_dataurl(url)
        icon = Icon(label=group["Name"], url=url)
        icons.append(icon)

        for item in group["MapFiltersChildren"]:
            # e.g. {
            #   "Rating": false,
            #   "Address": "המלך ג'ורג' 44, ירושלים",
            #   "Longitude": "35.215791827115616",
            #   "Latitude": "31.777267365823803",
            #   "HasPage": true,
            #   "CategoryId": 0,
            #   "Facility": null,
            #   "FacilityType": null,
            #   "InstituteData": null,
            #   "Link": null,
            #   "Id": 24528,
            #   "ParentId": 5650,
            #   "Name": "חניון בית אביחי",
            #   "ListName": null
            # }
            lon = item["Longitude"]
            lat = item["Latitude"].rstrip(",")
            if not lon or not lat:
                continue

            addr = item["Address"]

            # For some reason there are x36 duplicates at the time of this writing
            key = (lat, lon, addr)
            if key in seen:
                continue
            seen.add(key)

            name = f"{item['Name']} ({group['Name']})"
            desc = (
                ("כתובת", addr),
                ("תאריך עדכון", update_date),
            )

            places.append(Place(name=name, desc=desc, icon=icon, lon=float(lon), lat=float(lat)))

    return Map(icons=icons, places=places)


def download_data(data_dir: Path):
    user_agent = get_fair_user_agent()
    response = requests.post(
        url=BASE_URL,
        data='{"Culture":"he-IL","Id":5502}',
        headers={
            "content-type": "application/json; charset=UTF-8",
            "user-agent": user_agent,
        },
    )
    response.raise_for_status()

    out_path = data_dir / JSON_NAME
    dump(response.content, out_path)
