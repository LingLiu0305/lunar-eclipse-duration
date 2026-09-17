# Total Lunar Eclipse Duration

![Totality duration of total lunar eclipses from 2021 to 2030](out/total-lunar-eclipse-duration.png)

## The phenomenon

A lunar eclipse occurs when the Moon passes through Earth's shadow. This project focuses on total lunar eclipses, during which the entire Moon enters Earth's umbral shadow. The Moon becomes much darker and may appear red. I chose this phenomenon because every total lunar eclipse follows the same basic process, but the length of totality is not always the same. My picture compares how long the total phase lasts for eclipses occurring between 2021 and 2030.

## The source

The data comes from NASA Goddard Space Flight Center's [Lunar Eclipses: 2021–2030](https://eclipse.gsfc.nasa.gov/LEdecade/LEdecade2021.html) table. Each row represents one lunar eclipse and includes its date, type, umbral magnitude, duration, and geographic region of visibility. `fetch.py` downloads the original HTML page once and saves the unchanged response in `data/`. The plotting script selects rows whose eclipse type is `Total`. NASA gives two durations for these rows; this project uses the second value, which is the duration of totality rather than the longer interval that also includes the partial phases. The durations are converted from hours and minutes into minutes before plotting.

## What the picture shows

Each horizontal bar represents one total lunar eclipse, and its length shows the duration of totality in minutes. The lighter bar identifies the longest totality in this decade. The chart makes the differences in duration easy to compare, but it leaves out the Moon's path through Earth's shadow, the places from which each eclipse is visible, observing conditions, and the Moon's actual colour. The dark red palette is a visual choice and does not represent a colour measurement from NASA.

## Run it

```bash
uv run fetch.py
uv run plot.py
```

After the source page has been cached in `data/`, `plot.py` reads only the local file and can generate the picture without an internet connection.
