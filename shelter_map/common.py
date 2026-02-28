import base64
import json
import platform
import sys
import typing
from dataclasses import dataclass
from datetime import datetime, timezone
from functools import cache
from pathlib import Path

import requests

from . import __version__


@dataclass(frozen=True)
class Icon:
    label: str
    url: str


@dataclass
class Place:
    name: str
    desc: tuple[tuple[str, str], ...]
    icon: Icon
    lon: float
    lat: float


@dataclass
class Map:
    icons: list[Icon]
    places: list[Place]


class City(typing.Protocol):
    NAME: str

    def generate_map(self, data_dir: Path) -> Map: ...
    def download_data(self, data_dir: Path): ...


JsonValue = dict["JsonValue"] | list["JsonValue"] | int | bool | str | None
FieldMapping = dict[str, typing.Literal[True] | tuple[str, typing.Callable[[JsonValue, dict[str, JsonValue]], str]]]


@cache
def get_fair_user_agent() -> str:
    return (
        f"Python/{sys.version_info.major}.{sys.version_info.minor} "
        f"({platform.system()}) shelter_map/{__version__} requests/{requests.__version__}"
    )


def image_url_to_dataurl(url: str):
    response = requests.get(url, headers={"user-agent": get_fair_user_agent()})
    response.raise_for_status()
    content_type = response.headers["content-type"]
    return f"data:{content_type};base64,{base64.b64encode(response.content).decode()}"


@cache
def cached_image_url_to_dataurl(url: str):
    return image_url_to_dataurl(url)


def load(path: str | Path):
    path = Path(path)
    if path.name.endswith(".json"):
        with open(path, "r", encoding="utf-8") as fp:
            return json.load(fp)
    # elif path.name.endswith(".csv"):
    #     with open(path, "r", encoding="utf-8") as fp:
    #         # strip byte-order mark if it exists
    #         contents = fp.read().lstrip('\ufeff').splitlines()
    #         reader = csv.DictReader(contents)
    #         return list(reader)
    raise NotImplementedError("Only .json and .csv file readers are implemented")


def get_city_name(city: City):
    return getattr(city, "NAME", get_city_key(city))


def get_city_key(city: City):
    return city.__name__.rsplit(".", 1)[-1]


def identity(x, item=None):
    return x


def format_sqm(x, item=None):
    return f"{x} מר" if x else ""


def map_pairs(item: dict, mapping: FieldMapping, labels: dict = None):
    pairs = []
    for field, rule in mapping.items():
        value = item[field]
        if value is None:
            continue
        label = field
        if labels is not None:
            label = labels.get(field, field)
        if rule is not True:
            label, value_formatting = rule
            value = value_formatting(value, item)
        if not value:
            continue
        pairs.append((label, value))
    return pairs


def dump(data: bytes | str, path: str | Path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    is_bytes = isinstance(data, bytes)
    with open(path, "wb" if is_bytes else "wt", encoding=None if is_bytes else "utf-8") as fp:
        fp.write(data)


def get_update_date(path: Path) -> str:
    return (
        datetime.fromtimestamp(
            Path(path).stat().st_mtime,
            tz=timezone.utc,
        )
        .date()
        .isoformat()
    )
