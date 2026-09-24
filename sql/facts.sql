-- Model: facts. One table per parsed row type: exactly what the filings say.
--
--   filings (accession)            → doc_type, period, issuer_cik, issuer_name, ticker?
--   owners  (accession, owner_cik) → owner_name, is_director, is_officer, is_ten_pct
--   lines   (accession, line_no)   → traded, code?, shares?, price?
--
--   owners.accession ⊆ filings.accession,  lines.accession ⊆ filings.accession
--
-- Keys and foreign keys are declared, so the database itself rejects a row
-- that breaks I1 (keys are unique) or I2 (foreign keys hold).

CREATE TABLE filings (
    accession   VARCHAR PRIMARY KEY,
    doc_type    VARCHAR NOT NULL CHECK (doc_type IN ('4', '4/A')),
    period      DATE NOT NULL,
    issuer_cik  INTEGER NOT NULL,
    issuer_name VARCHAR NOT NULL,
    ticker      VARCHAR
);

CREATE TABLE owners (
    accession   VARCHAR NOT NULL REFERENCES filings (accession),
    owner_cik   INTEGER NOT NULL,
    owner_name  VARCHAR NOT NULL,
    is_director BOOLEAN NOT NULL,
    is_officer  BOOLEAN NOT NULL,
    is_ten_pct  BOOLEAN NOT NULL,
    PRIMARY KEY (accession, owner_cik)
);

CREATE TABLE lines (
    accession VARCHAR NOT NULL REFERENCES filings (accession),
    line_no   INTEGER NOT NULL,
    traded    DATE NOT NULL,
    code      VARCHAR,
    shares    DECIMAL(18, 6) CHECK (shares >= 0),
    price     DECIMAL(18, 6) CHECK (price >= 0),
    PRIMARY KEY (accession, line_no)
);
