-- Model: derived. Claims resolved by a stated rule.
--
--   companies (cik) → name, ticker?    each CIK takes what most of its filings say,
--   insiders  (cik) → name             ties going to the latest period
--
-- Filings can disagree about a name or ticker (a typo in one filing), so
-- cik → name only holds here, by this rule, not in the facts.

CREATE TABLE companies AS
SELECT issuer_cik AS cik, issuer_name AS name, ticker
FROM filings
GROUP BY issuer_cik, issuer_name, ticker
QUALIFY row_number() OVER (PARTITION BY issuer_cik ORDER BY count(*) DESC, max(period) DESC) = 1;

CREATE TABLE insiders AS
SELECT o.owner_cik AS cik, o.owner_name AS name
FROM owners o JOIN filings f USING (accession)
GROUP BY o.owner_cik, o.owner_name
QUALIFY row_number() OVER (PARTITION BY o.owner_cik ORDER BY count(*) DESC, max(f.period) DESC) = 1;
