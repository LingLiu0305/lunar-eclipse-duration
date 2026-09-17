# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "matplotlib"]
# ///

"""Read the cached NASA table and compare totality durations."""

import re
from pathlib import Path

import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

FILE = "nasa-lunar-eclipses-2021-2030.html"
PICTURE = "total-lunar-eclipse-duration.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def duration_to_minutes(text):
    """Convert a duration such as '01h25m' to a number of minutes."""
    match = re.fullmatch(r"(\d{2})h(\d{2})m", text.strip())
    if not match:
        raise ValueError(f"cannot read duration: {text!r}")
    hours, minutes = (int(part) for part in match.groups())
    return hours * 60 + minutes


def total_eclipses(path):
    """Return (date, minutes) pairs for total eclipses in NASA's decade table."""
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    eclipses = []

    for row in soup.select("tr"):
        cells = [cell.get_text(" ", strip=True) for cell in row.select("td")]
        if len(cells) < 6 or cells[2] != "Total":
            continue

        durations = re.findall(r"\d{2}h\d{2}m", cells[5])
        if len(durations) < 2:
            continue

        eclipses.append((cells[0], duration_to_minutes(durations[-1])))

    if not eclipses:
        raise ValueError("No total eclipses found. NASA may have changed the table.")
    return eclipses


def main():
    eclipses = total_eclipses(DATA)

    for date, minutes in eclipses:
        print(f"{date}: {minutes} minutes of totality")

    dates = [date for date, _ in eclipses]
    minutes = [minutes for _, minutes in eclipses]
    colors = ["#b33a3a" if value == max(minutes) else "#6f1d1b" for value in minutes]

    fig, ax = plt.subplots(figsize=(10, 6))
    bars = ax.barh(dates, minutes, color=colors)
    ax.bar_label(bars, labels=[f"{value} min" for value in minutes], padding=4)
    ax.set_xlabel("duration of totality (minutes)")
    ax.set_title("Total lunar eclipse duration, 2021–2030")
    ax.set_xlim(0, max(minutes) + 15)
    ax.invert_yaxis()
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=180)
    print(f"saved out/{PICTURE}")


if __name__ == "__main__":
    main()

