# Sets shared by every stage of the pipeline. Each name is defined once, here.

from datetime import date

Accession = str  # "dddddddddd-dd-dddddd": the SEC's id for one filing, never changes
Day = date
Bytes = bytes
