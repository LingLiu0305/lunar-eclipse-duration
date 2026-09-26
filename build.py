# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Build the offline lunar atlas from the unchanged NASA catalogue."""

import datetime as dt
import html
import json
from pathlib import Path
import re
import shutil

HERE = Path(__file__).resolve().parent
SOURCE = HERE / "data/nasa-lunar-eclipses-2001-2100.html"


def read_catalogue(path=SOURCE):
    """Keep all eclipse types, converting greatest TD to catalogue-based UT."""
    plain = html.unescape(re.sub(r"<[^>]+>", " ", path.read_text()))
    records = []
    for line in plain.splitlines():
        c = line.split()
        if len(c) != 18 or not re.fullmatch(r"\d{5}", c[0]):
            continue
        greatest_td = dt.datetime.strptime(" ".join(c[1:5]), "%Y %b %d %H:%M:%S")
        greatest_ut = greatest_td - dt.timedelta(seconds=int(c[5]))
        duration = lambda value: None if value == "-" else float(value)
        records.append({
            "id": c[0], "year": int(c[1]), "date": greatest_td.date().isoformat(),
            "greatestUT": greatest_ut.replace(tzinfo=dt.timezone.utc).timestamp() * 1000,
            "deltaT": int(c[5]), "type": c[8][0], "saros": int(c[7]),
            "gamma": float(c[10]), "penumbralMagnitude": float(c[11]),
            "umbralMagnitude": float(c[12]),
            "penumbralMinutes": duration(c[13]), "umbralMinutes": duration(c[14]),
            "totalMinutes": duration(c[15]),
            "source": f"https://eclipse.gsfc.nasa.gov/5MCLEmap/2001-2100/LE{greatest_td:%Y-%m-%d}{c[8][0]}.gif",
        })
    if len(records) != 228 or sum(r["type"] == "T" for r in records) != 85:
        raise ValueError("NASA catalogue does not contain the expected 228 / 85 records")
    return records


def build(destination=None):
    destination = Path(destination) if destination else HERE / "site"
    destination.mkdir(parents=True, exist_ok=True)
    records = read_catalogue()
    for path in (HERE / "web").iterdir():
        if path.is_file():
            shutil.copy2(path, destination / path.name)
    (destination / "eclipses.json").write_text(json.dumps(records, ensure_ascii=False, indent=2) + "\n")
    print(f"Built {destination}: {len(records)} eclipses, 2001–2100")
    return destination


if __name__ == "__main__":
    build()
