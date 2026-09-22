# Model: build
#
# State       R  : Accession → Bytes               the raw store (extract.py)
#             DB : the database, a pure function of R
#
# Build       build(R) = derived(facts(R))
#             facts    = for each a ∈ R: parse(a, xml(R[a])) → rows of filings, owners, lines
#             derived  = companies and insiders, resolved from the facts (sql/derived.sql)
#
# Every build starts from an empty database, so building twice gives the same tables (I4).

import argparse
from dataclasses import astuple
from pathlib import Path

import duckdb

from parse import parse, xml

SQL = Path(__file__).parent / "sql"
BATCH = 500  # rows per INSERT: DuckDB is slow row by row


def facts(raw: Path) -> dict[str, list[tuple]]:
    tables: dict[str, list[tuple]] = {"filings": [], "owners": [], "lines": []}
    for path in sorted(raw.glob("*.txt")):
        filing, owners, lines = parse(path.stem, xml(path.read_bytes()))
        tables["filings"].append(astuple(filing))
        tables["owners"] += [astuple(o) for o in owners]
        tables["lines"] += [astuple(line) for line in lines]
    return tables


def insert(con: duckdb.DuckDBPyConnection, table: str, rows: list[tuple]) -> None:
    for i in range(0, len(rows), BATCH):
        batch = rows[i:i + BATCH]
        placeholders = ", ".join(["(" + ", ".join("?" * len(batch[0])) + ")"] * len(batch))
        con.execute(f"INSERT INTO {table} VALUES {placeholders}", [v for row in batch for v in row])


def build(raw: Path, db: Path) -> None:
    tables = facts(raw)
    db.unlink(missing_ok=True)
    with duckdb.connect(str(db)) as con:
        con.execute((SQL / "facts.sql").read_text(encoding="utf-8"))
        for table, rows in tables.items():  # filings first: owners and lines point at it
            insert(con, table, rows)
        con.execute((SQL / "derived.sql").read_text(encoding="utf-8"))


def main() -> None:
    p = argparse.ArgumentParser(description="Build the database from data/raw.")
    p.add_argument("--raw", type=Path, default=Path("data/raw"))
    p.add_argument("--db", type=Path, default=Path("insiders.duckdb"))
    a = p.parse_args()
    build(a.raw, a.db)


if __name__ == "__main__":
    main()
