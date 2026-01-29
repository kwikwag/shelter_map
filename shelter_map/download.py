import argparse
from pathlib import Path

from .by_city import all_cities


def main(out_dir: str | Path = "data"):
    out_dir = Path(out_dir)
    for city in all_cities:
        city.download_data(out_dir)
    print("Done")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out-dir", default="data")
    args = parser.parse_args()

    main(out_dir=args.out_dir)
