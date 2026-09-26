# Lunar Passage — Interactive Century Poster

![Standalone, directly clickable lunar instrument](out/lunar-atlas.png)

```bash
uv run atlas.py
```

This opens a **standalone Python window**, with the controls embedded directly
in the artwork. No browser or web server is required. All interface text is English.

- Click a **coral bubble** to select and animate that total eclipse.
- The 85 equal-size bubbles move clockwise through the century.
  Radial distance is 170 + 1.48 × totality duration in canvas units.
  The inner offset makes room for the animated Moon; it does not indicate time.
- Hover the **outer year ring** to preview a year; click it, or use +/−,
  to enter that year's eclipse view. The first event starts playing.
- Click a **small Moon beneath the year** to select any eclipse in that year,
  including partial and penumbral events not plotted in the totality overview.
- Click the **central Moon or Play/Pause label** to pause or resume.
- Click or drag the **horizontal event timeline** to seek.
- The application starts with a still century overview. Selecting a year or
  eclipse opens a separate **focus layout in the same native window**. A large
  Moon, adjacent event information, top date selectors, and a long timeline
  replace the century diagram. **Back to century** pauses playback and returns
  with the selected year and event preserved and highlighted.
- **Data & phase details** reveals phase dates/times, full-event duration, scientific limits,
  and clickable time-zone and playback-speed settings. These are not permanent
  panels on the main canvas.
- **Browsing year** and **Eclipse n of N selected** distinguish the year from
  the current event. The event's catalogue date stays fixed in the information
  group beside the Moon; the animation date may change across midnight.
- **Playing**, **Paused**, and **Complete** show the current playback state,
  separately from the Play/Pause/Replay action. Seeking pauses the animation.
  Details temporarily pauses playback and restores its previous state on close.
- Overview and focus use different fixed Moon sizes (85 and 185 canvas units
  in radius). Views switch directly; there is no animated zoom or bounce.
- Press **F** for fullscreen and **I** for data notes and controls.

Keyboard: Left/Right changes year; Up/Down seeks; `[` / `]` changes event;
Space plays/pauses; R replays; S cycles speed; T changes the time basis.
Tab focuses controls and Enter activates them. `uv run atlas.py --paused`
starts with animation paused. The native window requires a desktop display.

The warm ivory, translucent coral bubbles, brown typography, and quiet teal
selection accents follow the editorial infographic reference. The earlier dense
instrument view remains in the source as a reusable rendering base; the default
entry point now opens the simplified poster. Each event plays
in 60 seconds at 1×, 30 seconds at 2×, or 15 seconds at 4×.

Typography uses Matplotlib's bundled STIXGeneral for editorial headings and
dates, DejaVu Sans for labels, and DejaVu Sans Mono for the animated clock.
No web font download or separate font installation is required. The original
font files remain in the installed Matplotlib package, with its bundled licenses.

![Selected eclipse with on-demand central information](out/lunar-atlas-selected.png)

## Original century artwork

![Animated century wheel of total lunar eclipses](out/lunar-eclipse-century-wheel.gif)

![Still image of the completed eclipse wheel](out/total-lunar-eclipse-duration.png)

## The phenomenon

A lunar eclipse occurs when the Moon passes through Earth's shadow. This project focuses on total lunar eclipses, during which the entire Moon enters Earth's umbral shadow. The Moon becomes much darker and may appear red. I chose this phenomenon because every total lunar eclipse follows the same basic process, but the length of totality is not always the same. My picture compares how long the total phase lasts across the 21st century.

## The source

The data comes from NASA Goddard Space Flight Center's [Catalog of Lunar Eclipses: 2001 to 2100](https://eclipse.gsfc.nasa.gov/LEcat5/LE2001-2100.html). Its 228 records describe the date, type, magnitude, phase durations, and location of greatest eclipse for every lunar eclipse in the century. `fetch.py` downloads the original HTML page once and saves the unchanged response in `data/`. The plotting script reads the fixed-width catalogue, selects its 85 total eclipses, and uses NASA's total-phase duration in minutes.

## What the picture shows

The animation builds a century wheel one eclipse at a time. Date moves clockwise around the circle, while distance from the centre, point size, and brightness respond to the duration of totality. The changing radius turns the sequence into an irregular orbit, and labels identify the shortest and longest events. This transformation shows rhythm and variation across the century, but it leaves out the Moon's path through Earth's shadow, visibility regions, observing conditions, and actual colour. The glowing palette is an artistic choice rather than a colour measurement from NASA.

## Run it

```bash
uv run fetch.py
uv run plot.py
uv run animate.py
```

After the source page has been cached in `data/`, `plot.py` reads only the local file and can generate the picture without an internet connection.

## Interaction and data — Week 04

**Interaction promise:** When I select a year, the interface plays that year's
first lunar eclipse and shows its changing date, time, and eclipse phase. I can
choose another eclipse in the same year, pause, replay, or drag the timeline.
The year ring covers 2001–2100 and provides access to
all 228 total, partial, and penumbral eclipses. The selected year refers to NASA's
catalogue date, independent of the display time offset. Once Python dependencies
are installed, the instrument uses only local files. The moon's generated texture
and displayed orientation are illustrative, not a measured lunar surface.

### Time and scientific limits

The source catalogue supplies greatest eclipse in Dynamical Time (TD). The
builder subtracts that row's ΔT to obtain the catalogue's Universal Time (UT),
following [NASA's field definitions](https://eclipse.gsfc.nasa.gov/LEcat5/LEcatkey.html).
Hong Kong display time is an approximate UT+8 conversion, not an exact future
civil-time prediction. Contact times are **symmetric estimates**: greatest
eclipse plus/minus half the published penumbral, umbral, or total duration.
The catalogue does not provide individual contact times. Estimates are marked
with a `~` in the native interface. The model fits these contacts and the maximum umbral magnitude;
it is not a physical ephemeris, real footage, or a forecast of actual moon colour.
Local visibility and weather are not represented. Dates update across midnight.

### Build and verify

```bash
uv run atlas.py --snapshot out/lunar-atlas.png
uv run --with matplotlib --with numpy --with pillow python -m unittest discover -s tests
```

`atlas.py` renders the native instrument; `eclipse_model.py` holds its English
phase labels, contact estimates, playback state, and illustrative geometry.
`build.read_catalogue` reads the unchanged NASA HTML. Tests verify every year's
ring selection, the actual click and key handlers, date rollover, and contact
geometry for every eclipse. The existing century PNG/GIF remain available.

The earlier browser prototype (`web/`, `serve.py`, and `build.py`'s site export)
is retained as development history. It is not needed to run the native instrument.
