# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///

"""Shared English-language timing model for the standalone lunar instrument."""

import datetime as dt
import math
import statistics

TYPES = {"T": "TOTAL LUNAR ECLIPSE", "P": "PARTIAL LUNAR ECLIPSE", "N": "PENUMBRAL ECLIPSE"}


def totality_context(records, event):
    """Compare only published total phases; absent totality is not zero-duration totality."""
    durations = sorted(row["totalMinutes"] for row in records if row["totalMinutes"] is not None)
    median = statistics.median(durations)
    selected = event["totalMinutes"]
    return {"durations": durations, "count": len(durations), "median": median,
            "minimum": min(durations), "maximum": max(durations), "selected": selected,
            "difference": None if selected is None else selected - median}


def phase_explanation(event, progress):
    name = phase(event, progress)
    if name == "ECLIPSE COMPLETE":
        return "The Moon has left Earth's shadow."
    if name == "GREATEST ECLIPSE":
        return "The deepest point of this eclipse."
    if name == "TOTALITY":
        return "The whole Moon is in Earth's dark shadow."
    if "UMBRA" in name and "PENUMBRA" not in name:
        return "Only part of the Moon is in dark shadow."
    return "The Moon is in Earth's faint outer shadow."


def phase_intervals(event):
    """Exclusive playback intervals, retaining the catalogue's nested durations."""
    points = [0, 1]
    for duration in [event["umbralMinutes"], event["totalMinutes"]]:
        if duration is not None:
            half = duration / event["penumbralMinutes"] / 2
            points.extend([.5 - half, .5 + half])
    points = sorted(points)
    intervals = []
    for start, end in zip(points, points[1:]):
        middle = (start + end) / 2
        minutes = abs(middle - .5) * event["penumbralMinutes"]
        kind = "penumbra"
        if event["umbralMinutes"] is not None and minutes < event["umbralMinutes"] / 2:
            kind = "partial"
        if event["totalMinutes"] is not None and minutes < event["totalMinutes"] / 2:
            kind = "totality"
        intervals.append((start, end, kind))
    return intervals


def milestones(event, progress):
    """Completed and next contact, based on the same time used by the animation."""
    points = contacts(event)
    now = time_at(event, progress)
    reached = [p for p in points if p[2] <= now + .01]
    upcoming = next((p for p in points if p[2] > now + .01), None)
    return reached[-1] if reached else points[0], upcoming


def contacts(event):
    greatest = event["greatestUT"]
    result = [("P1", "Penumbral entry", greatest - event["penumbralMinutes"] * 30000)]
    if event["umbralMinutes"] is not None:
        result.append(("U1", "Partial begins", greatest - event["umbralMinutes"] * 30000))
    if event["totalMinutes"] is not None:
        result.append(("U2", "Totality begins", greatest - event["totalMinutes"] * 30000))
    result.append(("MAX", "Greatest eclipse", greatest))
    if event["totalMinutes"] is not None:
        result.append(("U3", "Totality ends", greatest + event["totalMinutes"] * 30000))
    if event["umbralMinutes"] is not None:
        result.append(("U4", "Partial ends", greatest + event["umbralMinutes"] * 30000))
    result.append(("P4", "Penumbral exit", greatest + event["penumbralMinutes"] * 30000))
    return result


def time_at(event, progress):
    return event["greatestUT"] + (max(0, min(1, progress)) - .5) * event["penumbralMinutes"] * 60000


def clock(event, progress, offset=8):
    return dt.datetime.fromtimestamp(time_at(event, progress) / 1000, dt.timezone.utc) + dt.timedelta(hours=offset)


def phase(event, progress):
    minutes = (progress - .5) * event["penumbralMinutes"]
    if progress >= 1:
        return "ECLIPSE COMPLETE"
    if progress <= 0:
        return "PENUMBRAL ENTRY"
    if abs(minutes) < .2:
        return "GREATEST ECLIPSE"
    if event["totalMinutes"] is not None and abs(minutes) <= event["totalMinutes"] / 2:
        return "TOTALITY"
    if event["umbralMinutes"] is not None and abs(minutes) <= event["umbralMinutes"] / 2:
        return "ENTERING UMBRA" if minutes < 0 else "LEAVING UMBRA"
    return "ENTERING PENUMBRA" if minutes < 0 else "LEAVING PENUMBRA"


def shadow(event, progress):
    """Illustrative geometry fitted to magnitude and symmetric contact times."""
    radius = max(2.65, 2 * event["umbralMagnitude"] - 1 + .04)
    impact = radius + 1 - 2 * event["umbralMagnitude"]
    pen_radius = radius + 2 * (event["penumbralMagnitude"] - event["umbralMagnitude"])
    chord = lambda distance: math.sqrt(max(0, distance * distance - impact * impact))
    nodes = [(0, 0)]
    if event["totalMinutes"] is not None:
        nodes.append((event["totalMinutes"] / 2, chord(radius - 1)))
    if event["umbralMinutes"] is not None:
        nodes.append((event["umbralMinutes"] / 2, chord(radius + 1)))
    nodes.append((event["penumbralMinutes"] / 2, chord(pen_radius + 1)))
    elapsed = abs(progress - .5) * event["penumbralMinutes"]
    x = nodes[-1][1]
    for (a, x1), (b, x2) in zip(nodes, nodes[1:]):
        if elapsed <= b:
            x = x1 + (x2 - x1) * (elapsed - a) / (b - a)
            break
    return x * (-1 if progress < .5 else 1), impact * (-1 if event["gamma"] < 0 else 1), radius, pen_radius


class Playback:
    """UI-independent state used by clicks, keys and the animation timer."""

    def __init__(self, records, year=2026):
        self.records = records
        self.offset = 8
        self.speed = 1
        self.select_year(year)

    def select_year(self, year):
        self.year = max(2001, min(2100, int(year)))
        self.events = [r for r in self.records if r["year"] == self.year]
        self.select_event(0)

    def select_event(self, index):
        self.index = index % len(self.events)
        self.event = self.events[self.index]
        self.progress = 0
        self.playing = True

    def seek(self, progress):
        self.progress = max(0, min(1, progress))
        self.playing = False

    def toggle(self):
        if self.progress >= 1:
            self.progress = 0
        self.playing = not self.playing

    def replay(self):
        self.progress = 0
        self.playing = True

    def advance(self, seconds):
        if self.playing:
            self.progress = min(1, self.progress + max(0, seconds) / 60 * self.speed)
            if self.progress >= 1:
                self.playing = False
