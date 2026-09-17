# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "matplotlib", "numpy"]
# ///

"""Turn NASA's century catalogue into a circular eclipse artwork."""

import datetime as dt
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
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


def wheel_coordinates(eclipses):
    """Map date to angle and totality duration to distance from the centre."""
    century_start = dt.date(2001, 1, 1)
    century_end = dt.date(2101, 1, 1)
    century_days = (century_end - century_start).days
    angles = [
        2 * np.pi * (date - century_start).days / century_days
        for date, _ in eclipses
    ]
    durations = [minutes for _, minutes in eclipses]
    return angles, durations


def draw_wheel(ax, eclipses, upto=None, show_extremes=True):
    """Draw some or all eclipses on a century-long polar timeline."""
    visible = eclipses if upto is None else eclipses[:upto]
    ax.clear()
    ax.set_theta_zero_location("N")
    ax.set_theta_direction(-1)
    ax.set_facecolor("#09070d")

    if visible:
        angles, durations = wheel_coordinates(visible)
        ax.plot(angles, durations, color="#8f3a43", linewidth=1.2, alpha=0.65)
        ax.fill(angles, durations, color="#651f36", alpha=0.14)
        ax.scatter(
            angles,
            durations,
            c=durations,
            cmap="inferno",
            vmin=0,
            vmax=110,
            s=[18 + value * 0.55 for value in durations],
            edgecolor="#ffd2a1",
            linewidth=0.45,
            zorder=3,
        )

    tick_years = [2001, 2021, 2041, 2061, 2081]
    tick_angles = [2 * np.pi * (year - 2001) / 100 for year in tick_years]
    ax.set_xticks(tick_angles, labels=[str(year) for year in tick_years])
    ax.tick_params(axis="x", colors="#d8c8cb", labelsize=9, pad=8)
    ax.set_ylim(0, 110)
    ax.set_yticks([20, 40, 60, 80, 100], labels=["20m", "40m", "60m", "80m", "100m"])
    ax.set_rlabel_position(286)
    ax.tick_params(axis="y", colors="#8f7c83", labelsize=8)
    ax.grid(color="#6e5660", alpha=0.28, linewidth=0.7)
    ax.spines["polar"].set_color("#70525d")
    ax.set_title(
        "A CENTURY OF TOTAL LUNAR ECLIPSES",
        color="#f2e8e4",
        fontsize=14,
        pad=24,
        fontweight="normal",
    )
    ax.text(
        0.5,
        0.5,
        "date moves clockwise\ndistance = minutes of totality",
        transform=ax.transAxes,
        ha="center",
        va="center",
        color="#bdaeb2",
        fontsize=9,
        linespacing=1.5,
    )

    if show_extremes and len(visible) == len(eclipses):
        angles, durations = wheel_coordinates(eclipses)
        for index, label, offset in (
            (min(range(len(durations)), key=durations.__getitem__), "shortest", (-100, -55)),
            (max(range(len(durations)), key=durations.__getitem__), "longest", (10, 4)),
        ):
            date, value = eclipses[index]
            ax.annotate(
                f"{label}\n{date:%Y %b %d} · {value:.1f} min",
                (angles[index], value),
                xytext=offset,
                textcoords="offset points",
                color="#f2e8e4",
                fontsize=8,
                arrowprops={"arrowstyle": "-", "color": "#8f7c83", "linewidth": 0.7},
            )


def main():
    eclipses = total_eclipses(DATA)

    print(f"{DATA.name}: {len(eclipse_rows(DATA))} eclipse records")
    print(f"{len(eclipses)} total eclipses; first one: {eclipses[0]}")
    print(f"duration is stored as {type(eclipses[0][1]).__name__}")

    fig, ax = plt.subplots(figsize=(8, 8), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#09070d")
    draw_wheel(ax, eclipses)
    fig.tight_layout()

    OUT.mkdir(exist_ok=True)
    fig.savefig(OUT / PICTURE, dpi=180)
    print(f"saved out/{PICTURE}")


if __name__ == "__main__":
    main()
