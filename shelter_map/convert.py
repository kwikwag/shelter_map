# With assistance from Claude
import argparse
import base64
import csv
import hashlib
import io
import json
import zipfile
from pathlib import Path
from xml.dom.minidom import Document

from .by_city import all_cities
from .common import Map, dump


def to_csv(map_: Map):
    """
    Produce CSV format for Google Maps import
    """
    # Define the essential columns for Google Maps
    csv_columns = [
        "Name",  # Location name
        "Latitude",  # Latitude coordinate
        "Longitude",  # Longitude coordinate
        "Description",  # Description/notes
    ]

    with io.StringIO() as fp:
        writer = csv.DictWriter(fp, fieldnames=csv_columns)
        writer.writeheader()

        for place in map_.places:
            row = {
                "Name": place.name,
                "Latitude": place.lat,
                "Longitude": place.lon,
                "Description": _pairs_to_csv(place.desc),
            }

            writer.writerow(row)

    return fp.getvalue()


SUBSTYLES = ["normal", "highlight"]


def to_kml(
    map_: Map,
    embed_dataurl_icons: bool = True,
    name: str = "Shelters",
):
    """
    Produce KML format for Google Maps import
    """
    doc = Document()

    def make_el(parent, tag, attrs=None, text=None, cdata=None):
        child = doc.createElement(tag)
        if attrs:
            for k, v in attrs.items():
                child.setAttribute(k, v)
        if text:
            child.appendChild(doc.createTextNode(text))
        if cdata:
            child.appendChild(doc.createCDATASection(cdata))
        parent.appendChild(child)
        return child

    # Create KML root element
    kml_elem = make_el(doc, "kml", attrs=dict(xmlns="http://www.opengis.net/kml/2.2"))
    document_elem = make_el(kml_elem, "Document")

    # Add document name
    make_el(document_elem, "name", text=name)

    # Create style for shelters
    style_map = {}
    attachments = {}
    for index, icon in enumerate(map_.icons):
        icon_id = f"icon-{index + 1}"
        style_map_id = f"icon-ci-{index + 1}"

        if embed_dataurl_icons:
            url = icon.url
        else:
            if icon.url.startswith("data:image/png;base64,"):
                archive_path = f"images/{icon_id}.png"
                attachments[archive_path] = base64.b64decode(icon.url.split(",", 1)[1])
                url = archive_path
            else:
                url = icon.url

        for substyle in SUBSTYLES:
            style_id = f"{style_map_id}-{substyle}"
            style_elem = make_el(document_elem, "Style", attrs=dict(id=style_id))
            icon_style_elem = make_el(style_elem, "IconStyle")
            # make_el(icon_style_elem, "scale", text="1")
            icon_elem = make_el(icon_style_elem, "Icon")
            # make_el(icon_style_elem, "hotSpot", attrs=dict(x="32", xunits="pixels", y="64", yunits="insetPixels"))
            make_el(icon_elem, "href", text=url)
            # label_style_elem = make_el(style_elem, "LabelStyle")
            # make_el(label_style_elem, "scale", text="1" if substyle == "highlight" else "0")

        style_map_elem = make_el(document_elem, "StyleMap", attrs=dict(id=style_map_id))
        for substyle in SUBSTYLES:
            style_id_ref = f"#{style_map_id}-{substyle}"
            pair_elem = make_el(style_map_elem, "Pair")
            make_el(pair_elem, "key", text=substyle)
            make_el(pair_elem, "styleUrl", text=style_id_ref)

        style_map[icon] = style_map_id

    # Add placemarks for each feature
    for place in map_.places:
        placemark_elem = make_el(document_elem, "Placemark")

        style_id = style_map.get(place.icon)
        make_el(placemark_elem, "name", text=place.name)
        make_el(placemark_elem, "description", cdata=_pairs_to_html(place.desc))
        make_el(placemark_elem, "styleUrl", text=f"#{style_id}")

        point_elem = make_el(placemark_elem, "Point")
        make_el(point_elem, "coordinates", text=f"{place.lon},{place.lat},0")

    # Write KML file with proper formatting
    return doc.toprettyxml(indent="  ", encoding="UTF-8"), attachments


def _pairs_to_csv(pairs):
    return " | ".join(f"{k}: {v}" for k, v in pairs)


def _pairs_to_html(pairs):
    return "".join(f"<b>{k}:</b> {v}<br/>" for k, v in pairs)


def dump_kmz(contents, path, attachments):
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        with archive.open("doc.kml", "w") as fp:
            if isinstance(contents, str):
                with io.TextIOWrapper(fp, encoding="utf-8") as tfp:
                    tfp.write(contents)
            else:
                fp.write(contents)

        for path, attachment_contents in attachments.items():
            with archive.open(path, "w") as fp:
                fp.write(attachment_contents)


def export(map_: Map, name: str, out_dir: Path, base_name: str, format: str, max_per_file: int = 2_000):
    num_files = (len(map_.places) - 1) // max_per_file + 1
    for file_idx in range(num_files):
        suffix = "" if num_files == 1 else f".{file_idx + 1}"
        name_of_part = name if num_files == 1 else f"{name} ({file_idx + 1})"
        out_path = out_dir / f"{base_name}{suffix}.{format}"
        map_part = Map(icons=map_.icons, places=map_.places[file_idx * max_per_file : (file_idx + 1) * max_per_file])
        if format == "csv":
            dump(to_csv(map_=map_part), out_path)
        elif format in {"kml", "kmz"}:
            contents, attachments = to_kml(map_=map_part, embed_dataurl_icons=format == "kml", name=name_of_part)
            if format == "kml":
                assert not attachments
                dump(contents, out_path)
            elif format == "kmz":
                dump_kmz(contents, out_path, attachments=attachments)
        else:  # both
            raise NotImplementedError("Invalid format")

        print(f"Output to: {out_path.as_posix()}")
    digest = map_hash(map_)
    print(f"Hash: {out_path.name}:{digest.hex()}")
    return digest


def map_hash(map_: Map) -> str:
    icon_lookup = {icon.url: index for index, icon in enumerate(map_.icons)}

    return hashlib.sha256(
        json.dumps(
            {
                "icons": [{"label": icon.label, "url": icon.url} for icon in map_.icons],
                "places": [
                    {
                        "name": place.name,
                        "desc": [(str(k), str(v)) for k, v in place.desc],
                        "icon": icon_lookup[place.icon.url],
                        "lon": float(place.lon),
                        "lat": float(place.lat),
                    }
                    for place in map_.places
                ],
            },
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8")
    ).digest()


def main():
    parser = argparse.ArgumentParser(description="Dump Google Maps formats")
    parser.add_argument("--data-dir", help="Path to data dir", default="data")
    parser.add_argument("--format", help="Output format", choices=["csv", "kml", "kmz"], default="kml")
    args = parser.parse_args()

    format = args.format
    if format not in {"kml", "kmz", "csv"}:
        parser.error("Output file extension should be .kml or .csv")

    data_dir = Path(args.data_dir)

    combined_hash = hashlib.sha256()

    for city in all_cities:
        city_map = city.generate_map(data_dir)
        module_name = city.__name__.rsplit(".", 1)[-1]
        digest = export(
            map_=city_map,
            name=f"{city.NAME} Shelters",
            out_dir=data_dir,
            base_name=f"{module_name}_shelters",
            format=format,
        )
        combined_hash.update(digest)

    print("Combined hash:", combined_hash.hexdigest())


if __name__ == "__main__":
    main()
