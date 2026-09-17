# /// script
# requires-python = ">=3.10"
# dependencies = ["beautifulsoup4", "matplotlib", "numpy", "pillow"]
# ///

"""Animate a century of total lunar eclipses as a growing circular trace."""

from pathlib import Path

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation, PillowWriter

from plot import DATA, draw_wheel, total_eclipses

HERE = Path(__file__).parent
OUT = HERE / "out"
PICTURE = "lunar-eclipse-century-wheel.gif"
FPS = 10
HOLD_FRAMES = 15


def main():
    eclipses = total_eclipses(DATA)
    fig, ax = plt.subplots(figsize=(6.5, 6.5), subplot_kw={"projection": "polar"})
    fig.patch.set_facecolor("#09070d")

    def frame(frame_number):
        """Reveal one more eclipse, then hold on the completed century."""
        count = min(frame_number + 1, len(eclipses))
        draw_wheel(ax, eclipses, upto=count, show_extremes=count == len(eclipses))
        date, minutes = eclipses[count - 1]
        ax.text(
            0.5,
            0.37,
            f"{date:%Y %b %d}\n{minutes:.1f} minutes",
            transform=ax.transAxes,
            ha="center",
            va="center",
            color="#ffb26f",
            fontsize=10,
            linespacing=1.4,
        )

    frames = len(eclipses) + HOLD_FRAMES
    animation = FuncAnimation(fig, frame, frames=frames, interval=1000 / FPS)
    OUT.mkdir(exist_ok=True)
    animation.save(OUT / PICTURE, writer=PillowWriter(fps=FPS), dpi=90)
    plt.close(fig)
    print(f"saved out/{PICTURE} ({(OUT / PICTURE).stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
