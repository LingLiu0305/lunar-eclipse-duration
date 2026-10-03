# Process

## Moonlit Navy theme — 3 October 2026

I selected the Moonlit Navy option proposed by Codex: deep navy, soft white
text, blue-grey data points, and amber interaction accents. The UI/UX review
emphasised contrast and retained outlines so colour is not the only selection
cue. I rejected the design search's neon/glitch suggestions; they would compete
with the data. Layout, data encoding, and playback remain unchanged. The Moon's
illustrative red eclipse shading is independent of the UI palette. A regression
test checks text contrast against the dark background in overview, playback,
and details, alongside rendered preview inspection.

## Tools used

I used ChatGPT to help me understand the assignment requirements, identify a suitable public data source, and create the first working structure of the project. I also used it to explain the difference between a downloadable data file and a table published directly on a web page. The eclipse data itself comes from NASA's published catalogue.

## One thing I kept

I kept the suggestion to cache NASA's original HTML page in `data/` and parse the saved page locally. NASA does not provide a JSON or CSV download button on this page, but the HTML table is still a published data source. Keeping the raw response follows the assignment's “fetch once” rule and allows the plotting script to run without internet access. It also preserves evidence of exactly which source data was used to make the picture.

## One thing I rejected

I rejected the initial assumption that NASA would provide a separate JSON download. I also rejected both the first horizontal bar chart and a conventional time-series plot. The bars became crowded after expanding to 85 eclipses, while the time series explained the values but did not express the repeating astronomical character of the subject. Instead, the program parses NASA's fixed-width catalogue and maps the century around a circle, revealing each eclipse in an animation.

## What I will review next

I still need to review whether using distance, point size, and brightness for the same duration adds useful emphasis or unnecessary repetition. The connecting line is an artistic trace through separate events rather than a continuous physical measurement, so the README states what the transformation shows and what it leaves out.

## Week 04 — interactive extension

I asked Codex to make selecting a specific year play that year's lunar eclipse
process, with date and time labels. I supplied three visual references featuring
radial instruments, fine technical annotations, pale backgrounds, and blue/red
accents. Codex implemented a local static interface, a NASA catalogue builder,
and an illustrative moon-shadow animation. Its UI/UX guidance informed keyboard
controls, mobile layouts, visible focus, and reduced-motion handling; the supplied
references guided the actual visual direction.

The extension keeps the cached NASA data and uses real published eclipse types,
durations, and magnitudes. It includes partial and penumbral events so selecting
a year without a total eclipse still produces an honest view of that year.
The date/time display converts TD to UT using each row's ΔT. The implementation
does not label the published TD value as a local clock time or claim the inferred
contact times are exact: contacts are estimated symmetrically from phase durations.
The interface explicitly describes that assumption and the artistic lunar texture,
orientation, and colour. The animated shadow follows the published phase durations
and greatest umbral magnitude, not a fully calculated physical orbit.

The reusable Python checks cover catalogue counts and a known TD-to-UT conversion.
JavaScript checks cover contact order, all eclipse types, cross-midnight date
changes, and shadow/contact consistency across the full century.

## Revision — direct interaction with the artwork

I rejected the webpage presentation after reviewing the first version. I wanted
to click inside the central image, with an entirely English interface, following
the reference's black/white split and blue orbital connections. Codex replaced
the main experience with a standalone Matplotlib window: years on the outer ring,
eclipses as connected nodes, phase seeking on the inner arc, and play/pause on
the Moon itself. A small notes overlay explains controls and scientific limits.

The native version reuses the cached source and the same transparent timing
assumptions. Its checks exercise actual pointer and keyboard callbacks, all 100
year positions, the full catalogue's contact geometry, and date rollover. The
generated snapshot is an output from the working instrument, not a mockup.

## Revision — information clarity

I kept the standalone artwork and its direct interactions, but asked for clearer
data communication. The revised phase key spells out P1/U1/U2/MAX/U3/U4/P4 and
shows dates and times beside clickable rows. Full-event duration and totality
have separate, prominent values. A shared colour legend connects the time arc
to an event-duration strip: the partial segments exclude totality, so the stages
do not double-count time. The playback clock, elapsed duration, and next milestone
are explicitly labelled. Decorative lines are lighter and specialist Saros and
magnitude values move into the notes, leaving the main display focused on timing.

The next clarity pass made the original question explicit: how long does totality
last? A labelled dot distribution now compares the selected duration with the
85 total eclipses in the cached century catalogue and their median. Partial and
penumbral events are excluded, not converted to zero-duration total eclipses.
Larger dates and phase labels, plus a plain-English explanation of the current
shadow stage, make the numbers and animated image easier to connect.

## Design review — hierarchy and interaction affordances

The screenshot review showed that the oversized title and playback clock competed
with the main duration question, while the century comparison appeared too early
in the reading order. The revised right-hand hierarchy is selected event,
duration summary, animation clock and timeline, next milestone, then century
context. Totality is the primary numeric emphasis; the title is slightly smaller.
The central artwork and standalone native form are preserved.

Duplicate clock labels were removed from the arc, leaving full times in the
clickable phase key. The highlighted row now explicitly means the last milestone
reached. A visible accelerated-playback caption states the seconds per full event.
Event text and the Play/Pause caption now respond to clicks, and the horizontal
timeline supports dragging. New callback tests cover these targets and all four
event labels in 2009. The UI/UX review informed grouping, contrast, and consistent
click targets; its generic website layout suggestions were not applied.

## Revision — a visual-first century poster

The user found the instrument too dense and chose the warm meteorite infographic
as the new visual direction. The default native application now opens a paper-like
poster: translucent coral bubbles replace the connected polygon, while the original
clockwise chronology and radial totality-duration mapping remain. Bubble area also
encodes totality, with a matching size legend. No decorative data points or geographic
map were added. Teal marks selection, not a new scientific category.

The phase table and technical details move to an on-demand overlay. The main view
keeps year selection, a central animated Moon, the selected eclipse's duration and
clock, and a simple scrubber. All 228 eclipses remain accessible through year controls;
only the 85 total eclipses belong in the century bubble graphic. The original century
PNG and GIF are preserved. The UI/UX skill informed the reduced hierarchy and spacing;
the user's reference determined the palette and editorial style.

## Approved iteration — overview, selection, details

After reviewing the Week 04 principle of one control and one clear response,
the user approved progressive disclosure, reduced bubble-size encoding, and
removal of the persistent right-hand information panel. Startup is now a still
century overview. Selecting a year plays its first eclipse; selecting a bubble
or thumbnail selects that exact event. The central Moon then shows the changing
date/time, type, totality duration, and a scrubber. A teal connector identifies
the selected total-eclipse data point without moving it.

All 85 plotted bubbles now have equal size; radial distance alone encodes duration,
with sparse minute labels. Details contains contact times, full-event duration,
time-zone and speed settings, and estimation notes. Overview restores the quiet
view. Years without total eclipses have an explicit message but still offer their
partial and penumbral events. Tests cover initial state, selection, return to
overview, settings, year mapping, cross-midnight dates, and playback callbacks.

## Iteration — clear feedback and editorial typography

The next approved pass addressed the Week 04 requirement that a control produce
a clear response. Browsing year, selected event index, fixed event date, and
animated date now have distinct roles. Playing/Paused/Complete state text is
separate from the available action. Details remembers whether playback was
running and restores that state on close; pointer and keyboard settings agree.
Regression tests were written and observed failing before these state changes.

The UI/UX review also informed a right-shifted, larger radial composition,
more visible equal-size bubbles, 0/50/100-minute scales, a clockwise arrow,
near-node hover readouts, and grouped outlined controls. STIXGeneral headings
and dates give an editorial atlas character; body labels remain sans-serif
and animated time uses monospaced digits. All fonts are bundled with Matplotlib.
The illustrative Moon keeps a stable size across overview/selection and its
generated texture is softened. No geographic data or new datasets were added.

## Selection motion

At the user's request, selection now enlarges the central Moon from its overview
radius of 60 to 74 canvas units, peaking briefly at 78. Two smoothstep segments
complete in 550 ms, without moving labels or changing the scientific timing.
Switching events restarts from the current visual radius, so rapid selection
does not snap to a fixed starting size. Pausing or seeking does not retrigger it;
the transition finishes independently of eclipse playback. Returning to Overview
restores the smaller Moon. Tests check growth, settling, fixed labels, paused
completion, and reset. The GIF preview is rendered from the actual application.

The user rejected this motion after reviewing it. The zoom and settling effect
were removed, restoring the fixed 70-unit Moon radius in every view. Selection
still updates the event and playback directly. The earlier motion GIF is an
obsolete experiment, not a preview of the current application.

## Separate century and year-focus layouts

The user approved replacing the cramped central detail area with a dedicated
focus layout in the same native window. Clicking a year or eclipse now navigates
directly to a 370-unit-diameter Moon, compared with 170 units in the overview.
The old pre-change central Moon was 140 units across. There is no zoom animation.
Event dates appear across the top, event identity and animation readouts sit
beside the Moon, and a 1050-unit timeline supplies a generous seek target.

The century view has larger 26-unit dots with 36-unit pointer targets. Hovering
a year highlights its total eclipses without selecting it. Clicking navigates,
so a drag cannot accidentally continue against the now-invisible year ring.
Back to century preserves the chosen year and event and pauses playback. The
main century graphic remains limited to total eclipses; all event types remain
accessible through the year view. Regression checks cover navigation, enlarged
but stable focus geometry, same-year event selection, return state, hover preview,
playback, settings, and cross-midnight dates.

## Revision — direct time and duration comparison

The circular overview remained visually distinctive, but user review showed that
its data meaning was not immediate. A century is a bounded timeline rather than a
natural cycle, and radial distance made values at different angles harder to
compare. I therefore replaced the overview wheel with a Cartesian scatter plot.
The horizontal axis now gives the eclipse date from 2001 to 2100, the vertical
axis gives totality duration in minutes, and every equal-size dot is one total
lunar eclipse. The question “How long does a total lunar eclipse last?” is the
main chart title; axis titles and units are printed on the picture itself.

The approved editorial system remains: ivory background, coral data marks, brown
typography, and teal selection feedback. A quiet teal band marks the browsing
year. Hovering that year emphasizes its dots; clicking the chart opens the year,
while clicking a dot opens the exact eclipse. The separate large-Moon focus view
is unchanged. This iteration deliberately rejects connecting lines, variable dot
sizes, and a decorative central Moon in the overview because they would imply
additional measurements or orbital geometry that the data does not contain.
# Readability refinement — 3 October 2026

Using Codex, I refined the existing scatter-plot overview instead of returning
to the radial artwork. I kept the warm paper palette and serif headline, but
removed the large introductory sidebar so the data occupies most of the width.
The headline gives the rounded observed catalogue range (5–103 minutes), while
the two extreme annotations retain exact durations (4.7 and 103.0 minutes).
The subtitle limits the claim to the total phase and the years 2001–2100;
the source footer notes that the catalogue includes future predictions.

I separated browsing from playback: choosing a year only highlights its band
and updates date buttons; choosing a specific eclipse opens the existing large
Moon view. Clicking empty plot space now does nothing. This rejects implicit
navigation and avoids making the user read instructions to predict an action.
Tests cover these state transitions, the extrema, and existing playback flows.
Rendered previews are checked for layout, but this is not a first-time-user
comprehension study or a claim of measured usability improvement.
