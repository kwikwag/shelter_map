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


def load(json_path):
    with open(json_path, "r", encoding="utf-8") as file:
        return json.load(file)


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
