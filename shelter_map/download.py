import argparse
import logging
from pathlib import Path

from .by_city import all_cities


logger = logging.getLogger(__name__)


def main(out_dir: str | Path = "data"):
    out_dir = Path(out_dir)
    for city in all_cities:
        name = getattr(city, "NAME", city)
        logger.info("Downloading data for %s", name)
        city.download_data(out_dir)
        logger.debug("Finished downloading data for %s", name)
    logger.info("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data")
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(levelname)s:%(name)s:%(message)s",
    )

    main(out_dir=args.out_dir)
