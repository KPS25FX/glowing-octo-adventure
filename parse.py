# Model: parse
#
# Sets        Accession, Day, Bytes (from sets.py); CIK (int > 0), Qty (exact decimal ≥ 0), Text (non-empty str)
#             X?   = X or None (missing). Absent, empty and whitespace-only all read as None.
#             DocType = {4, 4/A}
#             Code    = {P, S, V, A, D, F, I, M, C, E, H, O, X, G, L, W, Z, J, K, U}
#
# Rows        Filing = accession, doc_type, period, issuer_cik, issuer_name, ticker?   (1 per file)
#             Owner  = accession, owner_cik, owner_name, is_director, is_officer,
#                      is_ten_pct                                                    (1 per reportingOwner)
#             Line   = accession, line_no, traded, code, shares?, price?            (1 per transaction)
#
# Readers     text    : Element × Path → Text?   the value at a path; <value> wrappers unwrapped
#             required: Element × Path → Text    text, where missing is an error
#             cik     : Element × Path → CIK
#             day     : Element × Path → Day
#             qty     : Element × Path → Qty?    missing is None, never 0
#             flag    : Element × Path → Bool    "1"/"true" or "0"/"false"; absent is False
#             one_of  : Element × Path × Set → member of Set
#             Every reader returns a value or raises ParseError(path, value): never a guess.
#
# Pure        xml     : Bytes → Element          cut <XML>…</XML> out of the raw .txt
#             parse   : Accession × Element → Filing × [Owner] × [Line]

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import get_args, Literal
from xml.etree.ElementTree import Element, fromstring

from sets import Accession, Bytes, Day

CIK = int
Qty = Decimal
DocType = Literal["4", "4/A"]
Code = Literal["P", "S", "V", "A", "D", "F", "I", "M", "C", "E",
               "H", "O", "X", "G", "L", "W", "Z", "J", "K", "U"]

TRANSACTION_PATHS = "nonDerivativeTable/nonDerivativeTransaction", "derivativeTable/derivativeTransaction"


class ParseError(ValueError):
    def __init__(self, path: str, value: str | None):
        super().__init__(f"{path}: {value!r}")


# Rows

@dataclass(frozen=True)
class Filing:
    accession: Accession
    doc_type: DocType
    period: Day
    issuer_cik: CIK
    issuer_name: str
    ticker: str | None


@dataclass(frozen=True)
class Owner:
    accession: Accession
    owner_cik: CIK
    owner_name: str
    is_director: bool
    is_officer: bool
    is_ten_pct: bool


@dataclass(frozen=True)
class Line:
    accession: Accession
    line_no: int
    traded: Day
    code: Code
    shares: Qty | None
    price: Qty | None


# Readers

def text(el: Element, path: str) -> str | None:
    s = el.findtext(f"{path}/value")
    if s is None:
        s = el.findtext(path)
    return s.strip() or None if s is not None else None


def required(el: Element, path: str) -> str:
    s = text(el, path)
    if s is None:
        raise ParseError(path, s)
    return s


def cik(el: Element, path: str) -> CIK:
    s = required(el, path)
    if not s.isdigit() or int(s) == 0:
        raise ParseError(path, s)
    return int(s)


def day(el: Element, path: str) -> Day:
    s = required(el, path)
    try:
        return date.fromisoformat(s[:10])  # some dates carry a timezone suffix
    except ValueError:
        raise ParseError(path, s) from None


def qty(el: Element, path: str) -> Qty | None:
    s = text(el, path)
    if s is None:
        return None
    try:
        q = Decimal(s.replace(",", ""))
    except InvalidOperation:
        raise ParseError(path, s) from None
    if not q.is_finite() or q < 0:
        raise ParseError(path, s)
    return q


def flag(el: Element, path: str) -> bool:
    s = text(el, path)
    if s is None:
        return False  # the form only requires the boxes that apply
    if s.lower() in ("1", "true"):
        return True
    if s.lower() in ("0", "false"):
        return False
    raise ParseError(path, s)


def one_of[T](el: Element, path: str, closed: type[T]) -> T:
    s = required(el, path)
    if s not in get_args(closed):
        raise ParseError(path, s)
    return s  # type: ignore[return-value]


# Pure

def xml(data: Bytes) -> Element:
    document = data.decode("latin-1")
    start, end = document.find("<XML>"), document.find("</XML>")
    if start == -1 or end == -1:
        raise ParseError("<XML>", None)
    return fromstring(document[start + len("<XML>"):end].strip())


def parse(accession: Accession, root: Element) -> tuple[Filing, list[Owner], list[Line]]:
    filing = Filing(
        accession=accession,
        doc_type=one_of(root, "documentType", DocType),
        period=day(root, "periodOfReport"),
        issuer_cik=cik(root, "issuer/issuerCik"),
        issuer_name=required(root, "issuer/issuerName"),
        ticker=text(root, "issuer/issuerTradingSymbol"),
    )
    owners = [
        Owner(
            accession=accession,
            owner_cik=cik(o, "reportingOwnerId/rptOwnerCik"),
            owner_name=required(o, "reportingOwnerId/rptOwnerName"),
            is_director=flag(o, "reportingOwnerRelationship/isDirector"),
            is_officer=flag(o, "reportingOwnerRelationship/isOfficer"),
            is_ten_pct=flag(o, "reportingOwnerRelationship/isTenPercentOwner"),
        )
        for o in root.findall("reportingOwner")
    ]
    if not owners:
        raise ParseError("reportingOwner", None)
    lines = [
        Line(
            accession=accession,
            line_no=n,
            traded=day(t, "transactionDate"),
            code=one_of(t, "transactionCoding/transactionCode", Code),
            shares=qty(t, "transactionAmounts/transactionShares"),
            price=qty(t, "transactionAmounts/transactionPricePerShare"),
        )
        for n, t in enumerate((t for path in TRANSACTION_PATHS for t in root.findall(path)), start=1)
    ]
    return filing, owners, lines
