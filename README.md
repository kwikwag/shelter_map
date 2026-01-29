# Urban shelters in Israel

To add a map of shelters in currrently supported cities (Tel Aviv and Jerusalem), go to this link in your mobile device:

| https://goo.gl/maps/P2tPvyksfy7gCD3aA |
| -- |
| ![Shelter map](images/qrcode.svg) |


This repository includes the tools used to create the above map.
These are reponsible for downloading public shelter locations from Israeli municipalities and exporting them into Google Maps–friendly formats (CSV, KML, KMZ).

The outputs of this map are available through the [GitHub action workflow runs](https://github.com/kwikwag/shelter_map/actions/workflows/daily.yml) and are uploaded (manually) to a public Google MyMaps available here: 


## Quick start

Use Python 3.12 or newer. I use `uv` for virtual environment management.

```bash
uv venv venv
source venv/bin/activate  # On Windows use `venv\Scripts\activate`
uv pip install -r requirements.txt -c constraints.txt
uv pip install -e .
python -m shelter_map.download
python -m shelter_map.convert --format kmz
```

This downloads the latest shelter datasets into `data/` and generates KMZ archives per city that can be imported into Google Maps (or other GIS tools).

## Contribute

Please feel free to contribute.

Especially welcome is support for more municipalities. To add a new city, create a new module under `shelter_map/by_city/`, update `all_cities` in `__init__.py`, and implement the two required functions. Each implementation should return `Map` with populated `Icon` and `Place` instances.

## Contributing

Bug reports, new city implementations, and documentation improvements are welcome. Please read [`CONTRIBUTING.md`](CONTRIBUTING.md) for guidelines on environment setup, coding standards, and submitting pull requests.

## License

Released under the [MIT License](LICENSE). Contributions are accepted under the same license unless explicitly stated otherwise.
