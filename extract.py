# Model: extraction
#
# Sets        Day, Bytes, Accession (from sets.py); Url, Filename
#             Filename = "edgar/data/{cik}/{accession}.txt"
#
# State       R : Accession → Bytes                 the raw store, data/raw/{accession}.txt
#
# Addresses   folder      : Day → Url               the quarter folder holding day's index
#             listing_url : Day → Url               folder(day) + "index.json"
#             index_url   : Day → Url               folder(day) + "master.{yyyymmdd}.idx"
#             file_url    : Filename → Url          ARCHIVES + filename
#             raw_path    : Filename → Path         where R keeps a filing: raw/{accession}.txt
#
# Pure        accession   : Filename → Accession
#             published   : Bytes → Set(Day)        days with an index, from a folder listing
#             filings     : Bytes → Set(Filename)   Form 4s in an index, one per Accession
#
# I/O         fetch       : Url → Bytes             the only contact with the SEC
#             save(f, b)  : R ↦ R ∪ {accession(f) ↦ b}   the only change to R; bytes untouched
#
# Chains      day ─index_url──▶ Url ─fetch─▶ Bytes ─filings───▶ Set(Filename)   which filings exist on day
#             f   ─file_url───▶ Url ─fetch─▶ Bytes ─save(f, ·)─▶ R extended      store one filing
#             day ─listing_url▶ Url ─fetch─▶ Bytes ─published─▶ Set(Day)        which days have an index
#
# Extraction  extract_day(d) = { save(f, fetch(file_url(f))) : f ∈ filings(fetch(index_url(d))), f ∉ R }
#             extract(D)     = ⋃ extract_day(d) over d ∈ D ∩ published

import argparse
import json
import time
from datetime import date, datetime, timedelta
from pathlib import Path

import requests

from sets import Accession, Bytes, Day

Url = str
Filename = str

ARCHIVES: Url = "https://www.sec.gov/Archives/"
FORM_4 = {"4", "4/A"}


# Addresses

def folder(day: Day) -> Url:
    quarter = (day.month - 1) // 3 + 1
    return f"{ARCHIVES}edgar/daily-index/{day.year}/QTR{quarter}/"


def listing_url(day: Day) -> Url:
    return folder(day) + "index.json"


def index_url(day: Day) -> Url:
    return folder(day) + f"master.{day.strftime('%Y%m%d')}.idx"


def file_url(f: Filename) -> Url:
    return ARCHIVES + f


def raw_path(f: Filename, raw: Path) -> Path:
    return raw / f"{accession(f)}.txt"


# Pure

def accession(f: Filename) -> Accession:
    return Path(f).stem


def published(listing: Bytes) -> set[Day]:
    names = (item["name"] for item in json.loads(listing)["directory"]["item"])
    return {datetime.strptime(n, "master.%Y%m%d.idx").date() for n in names if n.startswith("master.")}


def filings(index: Bytes) -> set[Filename]:
    lines = index.decode("latin-1").splitlines()
    start = next(i for i, line in enumerate(lines) if line.startswith("---")) + 1
    rows = [line.split("|") for line in lines[start:]]
    # a filing is listed once per party (issuer and each owner), so keep one per accession
    return set({accession(f): f for cik, name, form, filed, f in rows if form in FORM_4}.values())


# I/O

def fetch(url: Url, user_agent: str) -> Bytes:
    time.sleep(0.2)  # SEC limit: 10 requests per second
    result = requests.get(url, headers={"User-Agent": user_agent}, timeout=30)
    result.raise_for_status()
    return result.content


def save(f: Filename, data: Bytes, raw: Path) -> None:
    partial = raw_path(f, raw).with_suffix(".part")  # a crash mid-write never looks saved
    partial.write_bytes(data)
    partial.replace(raw_path(f, raw))


# Extraction

def extract_day(day: Day, raw: Path, user_agent: str) -> int:
    new = 0
    for f in sorted(filings(fetch(index_url(day), user_agent))):
        if not raw_path(f, raw).exists():
            save(f, fetch(file_url(f), user_agent), raw)
            new += 1
    return new


def extract(days: list[Day], raw: Path, user_agent: str) -> None:
    raw.mkdir(parents=True, exist_ok=True)
    available = set().union(*(published(fetch(url, user_agent)) for url in {listing_url(d) for d in days}))
    for day in days:
        if day in available:
            print(f"{day}: {extract_day(day, raw, user_agent)} new")
        else:
            print(f"{day}: no index (weekend or holiday)")


def main() -> None:
    p = argparse.ArgumentParser(description="Download every Form 4 filed between two dates into data/raw.")
    p.add_argument("start", type=date.fromisoformat, help="first day, YYYY-MM-DD")
    p.add_argument("end", type=date.fromisoformat, help="last day, YYYY-MM-DD")
    p.add_argument("--user-agent", required=True, help='"Name email", required by the SEC')
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    a = p.parse_args()
    days = [a.start + timedelta(n) for n in range((a.end - a.start).days + 1)]
    extract(days, a.raw, a.user_agent)


if __name__ == "__main__":
    main()
