# Process

## Tools used

I used ChatGPT to help me understand the assignment requirements, identify a suitable public data source, and create the first working structure of the project. I also used it to explain the difference between a downloadable data file and a table published directly on a web page. The eclipse data itself comes from NASA's published catalogue.

## One thing I kept

I kept the suggestion to cache NASA's original HTML page in `data/` and parse the saved page locally. NASA does not provide a JSON or CSV download button on this page, but the HTML table is still a published data source. Keeping the raw response follows the assignment's “fetch once” rule and allows the plotting script to run without internet access. It also preserves evidence of exactly which source data was used to make the picture.

## One thing I rejected

I rejected the initial assumption that NASA would provide a separate JSON download. I also rejected the first horizontal bar chart after expanding the data from ten years to a full century: 85 labelled bars would be too crowded to read. Manual transcription would remove the connection to the original published file and could introduce mistakes. Instead, the program parses NASA's fixed-width catalogue and uses points to show the dates and durations of all 85 total eclipses.

## What I will review next

I still need to decide whether using both height and colour for duration adds useful emphasis or unnecessary repetition. I will also review whether the connecting line suggests a continuous measurement even though eclipses are separate events.
