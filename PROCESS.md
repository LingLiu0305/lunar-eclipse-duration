# Process

## Tools used

I used ChatGPT to help me understand the assignment requirements, identify a suitable public data source, and create the first working structure of the project. I also used it to explain the difference between a downloadable data file and a table published directly on a web page. The eclipse data itself comes from NASA's published catalogue.

## One thing I kept

I kept the suggestion to cache NASA's original HTML page in `data/` and parse the saved page locally. NASA does not provide a JSON or CSV download button on this page, but the HTML table is still a published data source. Keeping the raw response follows the assignment's “fetch once” rule and allows the plotting script to run without internet access. It also preserves evidence of exactly which source data was used to make the picture.

## One thing I rejected

I rejected the initial assumption that NASA would provide a separate JSON download. I also rejected both the first horizontal bar chart and a conventional time-series plot. The bars became crowded after expanding to 85 eclipses, while the time series explained the values but did not express the repeating astronomical character of the subject. Instead, the program parses NASA's fixed-width catalogue and maps the century around a circle, revealing each eclipse in an animation.

## What I will review next

I still need to review whether using distance, point size, and brightness for the same duration adds useful emphasis or unnecessary repetition. The connecting line is an artistic trace through separate events rather than a continuous physical measurement, so the README states what the transformation shows and what it leaves out.
