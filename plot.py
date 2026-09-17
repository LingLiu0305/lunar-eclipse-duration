# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "matplotlib"]
# ///

"""Read NASA's cached century catalogue and compare totality durations."""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt
from bs4 import BeautifulSoup

FILE = "nasa-lunar-eclipses-2001-2100.html"
PICTURE = "total-lunar-eclipse-duration.png"

HERE = Path(__file__).parent
DATA = HERE / "data" / FILE
OUT = HERE / "out"


def eclipse_rows(path):
    """Parse the fixed-width catalogue into lists of column values."""
    soup = BeautifulSoup(path.read_bytes(), "html.parser")
    rows = []

    for block in soup.select("pre"):
        for line in block.get_text(" ").splitlines():
            columns = line.split()
            if len(columns) == 18 and columns[0].isdigit() and len(columns[0]) == 5:
                rows.append(columns)

    if len(rows) != 228:
        raise ValueError(f"Expected 228 eclipse records, found {len(rows)}")
    return rows


def total_eclipses(path):
    """Return (date, minutes) pairs for all total eclipses in the catalogue."""
    eclipses = []

    for columns in eclipse_rows(path):
        eclipse_type = columns[8]
        if not eclipse_type.startswith("T"):
            continue

        date = dt.datetime.strptime(" ".join(columns[1:4]), "%Y %b %d").date()
        total_minutes = float(columns[15])
        eclipses.append((date, total_minutes))

    if len(eclipses) != 85:
        raise ValueError(f"Expected 85 total eclipses, found {len(eclipses)}")
    return eclipses


def main():
    eclipses = total_eclipses(DATA)

    print(f"{DATA.name}: {len(eclipse_rows(DATA))} eclipse records")
    print(f"{len(eclipses)} total eclipses; first one: {eclipses[0]}")
    print(f"duration is stored as {type(eclipses[0][1]).__name__}")

    dates = [date for date, _ in eclipses]
    minutes = [minutes for _, minutes in eclipses]
    shortest = min(range(len(minutes)), key=minutes.__getitem__)
    longest = max(range(len(minutes)), key=minutes.__getitem__)

    fig, ax = plt.subplots(figsize=(11, 5.5))
    ax.plot(dates, minutes, color="#d9b8ae", linewidth=1, zorder=1)
    points = ax.scatter(
        dates,
        minutes,
        c=minutes,
        cmap="Reds",
        edgecolor="#4c1715",
        linewidth=0.5,
        s=38,
        zorder=2,
    )
    for index, vertical_offset in ((shortest, 9), (longest, -18)):
        date, value = eclipses[index]
        ax.annotate(
            f"{date:%Y %b %d}\n{value:.1f} minutes",
            (date, value),
            xytext=(7, vertical_offset),
            textcoords="offset points",
            fontsize=9,
        )

    ax.set_ylabel("duration of totality (minutes)")
    ax.set_title("Total lunar eclipse duration across the 21st century")
    ax.set_ylim(0, 115)
    ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
    ax.spines[["top", "right"]].set_visible(False)
    colour_bar = fig.colorbar(points, ax=ax, pad=0.02)
    colour_bar.set_label("minutes")
    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=180)
    print(f"saved out/{PICTURE}")


if __name__ == "__main__":
    main()
