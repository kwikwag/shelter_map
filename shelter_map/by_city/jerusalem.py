import logging
import urllib.parse
from pathlib import Path

import requests

from ..common import Icon, Map, Place, dump, get_fair_user_agent, get_update_date, image_url_to_dataurl, load

logger = logging.getLogger(__name__)

NAME = "Jerusalem"
JSON_NAME = "jerusalem_shelters.json"
BASE_URL = "https://www.jerusalem.muni.il/umbraco/api/map/GetMapById"


def generate_map(data_dir: Path, icons_as_dataurls: bool = True):
    json_path = data_dir / JSON_NAME
    logger.debug("Reading: %s", json_path)

    data = load(json_path)
    update_date = get_update_date(json_path)
    logger.debug("Loaded. Update date: %s", update_date)

    icons = []
    places = []
    seen = set()
    dataurl_cache = {}
    n = 0

    for group in data:
        url = urllib.parse.urljoin(BASE_URL, group["Icon"])
        if icons_as_dataurls:
            dataurl = dataurl_cache.get(url)
            if dataurl is None:
                dataurl = image_url_to_dataurl(url)
                dataurl_cache[url] = dataurl
            url = dataurl
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
            n += 1
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

    logger.debug("Number of entries: %s, unique places: %s, icons: %s", n, len(places), len(icons))

    return Map(icons=icons, places=places)


def download_data(data_dir: Path):
    user_agent = get_fair_user_agent()
    headers = {
        "content-type": "application/json; charset=UTF-8",
        "user-agent": user_agent,
    }
    data = '{"Culture":"he-IL","Id":5502}'
    logger.debug(
        "Downloading: %s",
        dict(
            url=BASE_URL,
            data=data,
            headers=headers,
        ),
    )
    response = requests.post(
        url=BASE_URL,
        data=data,
        headers=headers,
    )
    response.raise_for_status()

    out_path = data_dir / JSON_NAME
    dump(response.content, out_path)
