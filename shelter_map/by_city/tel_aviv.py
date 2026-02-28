import logging
from pathlib import Path

import requests

from ..common import FieldMapping, Icon, Map, Place, dump, format_sqm, get_update_date, identity, load, map_pairs

logger = logging.getLogger(__name__)

NAME = "Tel Aviv"

BASE_URL = "https://gisn.tel-aviv.gov.il/arcgis/rest/services/IView2/MapServer"
SOURCE_URL = "https://www5.tel-aviv.gov.il/Tlv4U/Gis/Default.aspx?592"
SHELTERS_JSON = "tel_aviv_shelters.json"
SHELTERS_META_JSON = "tel_aviv_shelters_meta.json"
DESCRIPTION_MAPPING: FieldMapping = {
    "t_sug": ("סוג", identity),
    "hearot": True,
    "pail": True,
    "is_open": True,
    "maneger_name": True,
    "shetach_mr": ("שטח", format_sqm),
    "ms_miklat": True,
    "date_import": True,
    "__source": ("מקור המידע", identity),
}


def get_tel_aviv_json(layer: str, limit: int):
    url = f"{BASE_URL}/{layer}/query"

    params = {
        "f": "json",
        "resultOffset": 0,
        "resultRecordCount": limit,
        "where": "1=1",
        "orderByFields": "",
        "outFields": "*",
        "returnGeometry": False,
        "spatialRel": "esriSpatialRelIntersects",
    }

    logger.debug("Downloading data: %s", dict(url=url, params=params))
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.content


def get_tel_aviv_meta_json(layer: str):
    url = f"{BASE_URL}/{layer}"
    params = {
        "f": "pjson",
    }

    logger.debug("Downloading metadata: %s", dict(url=url, params=params))
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.content


def build_name(attrs):
    """Generate a meaningful name for the location"""
    name_parts = []
    for field in ["t_sug", "Full_Address"]:
        if attrs.get(field):
            name_parts.append(attrs[field])
    return " ".join(name_parts) if name_parts else "Unknown Location"


def get_icon_map(meta_data: dict):
    renderer = meta_data["drawingInfo"]["renderer"]
    assert renderer["field1"] == "t_sug"

    def make_url(symbol):
        return f"data:{symbol['contentType']};base64,{symbol['imageData']}"

    return {
        None: Icon(label=renderer["defaultLabel"], url=make_url(renderer["defaultSymbol"])),
        **{
            entry["value"]: Icon(label=entry["label"], url=make_url(entry["symbol"]))
            for entry in renderer["uniqueValueInfos"]
        },
    }


def generate_map(data_dir: Path):
    data_path = data_dir / SHELTERS_JSON
    meta_data_path = data_dir / SHELTERS_META_JSON
    logger.debug("Loading: data=%s, meta_data=%s", data_path, meta_data_path)

    data = load(data_path)
    meta_data = load(meta_data_path)

    update_date = get_update_date(data_path)
    logger.debug("Loaded. Update date: %s", update_date)

    aliases = data["fieldAliases"]

    icon_map = get_icon_map(meta_data=meta_data)

    places = []
    for feature in data["features"]:
        attrs = dict(feature["attributes"], __source=SOURCE_URL)

        # Skip if no coordinates
        if not attrs.get("lat") or not attrs.get("lon"):
            continue

        name = build_name(attrs)
        desc = map_pairs(attrs, mapping=DESCRIPTION_MAPPING, labels=aliases)
        icon = icon_map.get(attrs.get("t_sug"), icon_map[None])
        lon = float(attrs["lon"])
        lat = float(attrs["lat"])
        places.append(Place(name=name, desc=desc, icon=icon, lon=lon, lat=lat))

    icons = list(icon_map.values())

    logger.debug("Number of places: %s, icons: %s", len(places), len(icons))
    return Map(icons=icons, places=places)


def download_data(data_dir: Path, layer: str = "592", limit: int = 5_000):
    out_path = data_dir / SHELTERS_JSON
    meta_out_path = data_dir / SHELTERS_META_JSON
    dump(get_tel_aviv_json(layer=layer, limit=limit), out_path)
    dump(get_tel_aviv_meta_json(layer=layer), meta_out_path)
