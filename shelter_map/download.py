import argparse
import logging
from pathlib import Path

from .by_city import all_cities
from .common import City, get_city_key


logger = logging.getLogger(__name__)


def main(out_dir: str | Path = "data", city_modules: list[City] = all_cities):
    out_dir = Path(out_dir)
    for module in city_modules:
        name = getattr(module, "NAME", str(module))
        logger.info("Downloading data for %s", name)
        try:
            module.download_data(out_dir)
            logger.debug("Finished downloading data for %s", name)
        except Exception:
            logger.exception("Failed to download data for %s", name)

    logger.info("Done")


if __name__ == "__main__":
    all_cities_map = {get_city_key(module): module for module in all_cities}

    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data")
    parser.add_argument("--cities", nargs="+", default=["all"], choices=sorted(all_cities_map) + ["all"])
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    cities = args.cities
    if "all" in cities:
        cities = list(all_cities_map)
    city_modules = [all_cities_map[name] for name in cities]

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    main(out_dir=args.out_dir, city_modules=city_modules)
