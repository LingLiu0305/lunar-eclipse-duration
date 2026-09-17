# /// script
# requires-python = ">=3.10"
# dependencies = ["requests"]
# ///

"""Fetch NASA's lunar-eclipse table once and cache the raw HTML in data/."""

from pathlib import Path

import requests

URL = "https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html"
FILE = "nasa-lunar-eclipses-2021-2030.html"

HERE = Path(__file__).parent
DATA = HERE / "data"


def fetch(url, path):
    """Fetch once. If the cached file exists, leave it unchanged."""
    if path.exists():
        print(
            f"data/{path.name} is already here "
            f"({path.stat().st_size // 1024} KB). Delete it to fetch again."
        )
        return path

    DATA.mkdir(exist_ok=True)
    print(f"asking {url}")
    reply = requests.get(
        url,
        timeout=60,
        headers={"User-Agent": "SD5913 PolyU student data-visualisation project"},
    )
    reply.raise_for_status()
    path.write_bytes(reply.content)
    print(f"saved data/{path.name} ({path.stat().st_size // 1024} KB)")
    return path


if __name__ == "__main__":
    fetch(URL, DATA / FILE)

