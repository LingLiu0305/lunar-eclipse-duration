# Process

## Tools used

I used ChatGPT to help me understand the assignment requirements, identify a suitable public data source, and create the first working structure of the project. I also used it to explain the difference between a downloadable data file and a table published directly on a web page. The eclipse data itself comes from NASA's published catalogue.

## One thing I kept

I kept the suggestion to cache NASA's original HTML page in `data/` and parse the saved page locally. NASA does not provide a JSON or CSV download button on this page, but the HTML table is still a published data source. Keeping the raw response follows the assignment's “fetch once” rule and allows the plotting script to run without internet access. It also preserves evidence of exactly which source data was used to make the picture.

## One thing I rejected

I rejected the initial assumption that NASA would provide a separate JSON download. I also chose not to copy the eclipse values manually into a Python list. Manual transcription would remove the connection to the original published file, could introduce mistakes, and would make the project less reproducible. Instead, the program finds the total-eclipse rows in the cached table and converts their duration values into minutes.

## What I will review next

This is the first working version of the project. I still need to decide whether highlighting only the longest eclipse communicates enough, and whether the order, labels, and colours make the comparison clear. I will update this process record as I test and revise those choices.
