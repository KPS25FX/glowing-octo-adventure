# Model: dashboard
#
# View        (w, k) ↦ clusters(w, k)                 the screen: companies where ≥ k buyers bought within w days
#             c      ↦ purchases_of(c), buyers(w)|c   one company: its purchases, and buyers(c, d, w) over d
#
# The dashboard only reads: every number on screen is a SQL macro from sql/clusters.sql.
# If the database is missing it is built first (build.py), so a clean clone runs with one command.
#
# Run         streamlit run app.py

from pathlib import Path

import altair as alt
import duckdb
import streamlit as st

from build import build

DB = Path("insiders.duckdb")
RAW = Path("data/raw")
NO_TICKER = ("NONE", "N/A")  # private funds and unlisted issuers file with these


@st.cache_resource
def connect() -> duckdb.DuckDBPyConnection:
    if not DB.exists():
        with st.spinner("Building the database from data/raw (about 15 s, first run only)…"):
            build(RAW, DB)
    return duckdb.connect(str(DB), read_only=True)


st.set_page_config(page_title="Insider buying clusters", layout="wide")
con = connect()
st.title("Insider buying clusters")
st.caption("Companies where several independent insiders bought their own stock on the open market "
           "(Form 4, code P) within a few weeks of each other. A screen for research, not a signal.")

with st.sidebar:
    w = st.slider("Window w (days)", 1, 90, 30)
    k = st.slider("Minimum buyers k", 2, 10, 3)
    listed_only = st.checkbox("Listed companies only", True, help="Hide issuers with no ticker (NONE, N/A).")
    hide_programmes = st.checkbox("Hide one-day-one-price clusters", False,
                                  help="Every purchase on one date at one price: likely a company-run "
                                       "programme rather than independent decisions.")

filings, purchases = con.sql("SELECT (SELECT count(*) FROM filings), (SELECT count(*) FROM lines WHERE code = 'P')").fetchone()
clusters = con.execute("SELECT * FROM clusters(?, ?)", [w, k]).df()
if listed_only:
    clusters = clusters[clusters.ticker.notna() & ~clusters.ticker.isin(NO_TICKER)]
if hide_programmes:
    clusters = clusters[~clusters.one_day_one_price]

a, b, c = st.columns(3)
a.metric("Form 4 filings", f"{filings:,}")
b.metric("Open-market purchases", f"{purchases:,}")
c.metric("Companies clustering", len(clusters))

st.subheader("Clusters")
st.caption("Ranked by the most buyers inside any one window, then by the most recent window.")
st.dataframe(
    clusters.drop(columns="cik"), hide_index=True, width="stretch",
    column_config={
        "peak_buyers": st.column_config.NumberColumn("Peak buyers"),
        "latest_cluster": st.column_config.DateColumn("Latest cluster day"),
        "one_day_one_price": st.column_config.CheckboxColumn("One day, one price"),
    },
)

if clusters.empty:
    st.stop()

st.subheader("Company")
labels = dict(zip(clusters.cik, clusters.ticker.fillna("—") + " · " + clusters.name))
cik = int(st.selectbox("Company", list(labels), format_func=labels.get, label_visibility="collapsed"))
st.caption(f"Each point is a purchase date d with the number of distinct buyers in [d − {w - 1}, d]. "
           f"Dashed line: k = {k}.")

series = con.execute("SELECT d, buyers FROM buyers(?) WHERE cik = ? ORDER BY d", [w, cik]).df()
points = alt.Chart(series).mark_circle(size=80, opacity=1).encode(
    x=alt.X("d:T", title="Trade date"),
    y=alt.Y("buyers:Q", title="Distinct buyers", axis=alt.Axis(tickMinStep=1), scale=alt.Scale(domainMin=0)),
    tooltip=[alt.Tooltip("d:T", title="Date"), alt.Tooltip("buyers:Q", title="Buyers")],
)
threshold = alt.Chart(series).mark_rule(strokeDash=[4, 4], color="gray").encode(y=alt.datum(k))
st.altair_chart(points + threshold, width="stretch")

st.dataframe(
    con.execute("SELECT * FROM purchases_of(?)", [cik]).df(), hide_index=True, width="stretch",
    column_config={
        "traded": st.column_config.DateColumn("Traded"),
        "ten_pct": st.column_config.CheckboxColumn("10% owner"),
        "shares": st.column_config.NumberColumn(format="localized"),
        "price": st.column_config.NumberColumn(format="dollar"),
        "value": st.column_config.NumberColumn(format="dollar"),
    },
)
