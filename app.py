"""Streamlit explorer for the SQL analysis.  Run with:  streamlit run app.py"""
from __future__ import annotations

import sqlite3
from pathlib import Path

import pandas as pd
import streamlit as st

from playground import MAX_ROWS, QueryError, run, schema

ROOT = Path(__file__).parent
LOGO = ROOT / "assets" / "logo.png"
DB = ROOT / "data" / "chinook.sqlite"

st.set_page_config(page_title="Music Store SQL Analytics", page_icon=str(LOGO), layout="wide")
st.logo(str(LOGO), size="large")
st.title("Music Store SQL Analytics")
st.caption("Seven business questions answered in SQL on the Chinook digital music store, plus a live, read-only SQL playground.")


@st.cache_data
def q(sql: str) -> pd.DataFrame:
    with sqlite3.connect(f"file:{DB}?mode=ro", uri=True) as con:
        return pd.read_sql_query(sql, con)


@st.cache_data
def result(key: str) -> pd.DataFrame:
    return pd.read_csv(ROOT / "results" / f"{key}.csv")


queries = sorted((ROOT / "sql").glob("*.sql"))
labels = {f.stem: f.read_text().splitlines()[0].lstrip("- ").strip() for f in queries}

tab_dash, tab_q, tab_sql = st.tabs(["Overview", "Business questions", "SQL playground"])

with tab_dash:
    k = q(
        """select round(sum(Total), 2) revenue, count(*) orders, count(distinct CustomerId) customers,
                  round(avg(Total), 2) aov, min(InvoiceDate) first, max(InvoiceDate) last from Invoice"""
    ).iloc[0]
    a, b, c, d = st.columns(4)
    a.metric("Revenue", f"${k.revenue:,.2f}")
    b.metric("Orders", f"{k.orders:,}")
    c.metric("Customers", f"{k.customers:,}")
    d.metric("Average order", f"${k.aov:.2f}")
    st.caption(f"Invoices from {k['first'][:10]} to {k['last'][:10]}.")

    m = result("01_monthly_revenue")
    st.markdown("**Monthly revenue and 3-month average**")
    st.line_chart(m.set_index("month")[["revenue", "revenue_3mo_avg"]].rename(columns={"revenue": "Revenue", "revenue_3mo_avg": "3-month average"}), height=280)

    left, right = st.columns(2)
    with left:
        st.markdown("**Revenue by genre**")
        g = result("03_genre_share").head(10)
        st.bar_chart(g, x="genre", y="revenue", horizontal=True, sort="-revenue", height=320, x_label="", y_label="Revenue ($)")
    with right:
        st.markdown("**Top countries**")
        cty = result("02_country_performance").head(10)
        st.bar_chart(cty, x="country", y="revenue", horizontal=True, sort="-revenue", height=320, x_label="", y_label="Revenue ($)")

    left, right = st.columns(2)
    with left:
        st.markdown("**Customer segments (RFM)**")
        seg = result("04_rfm_segments")["segment"].value_counts().rename_axis("Segment").reset_index(name="Customers")
        st.bar_chart(seg, x="Segment", y="Customers", sort="-Customers", height=280)
    with right:
        st.markdown("**Cohort retention**")
        coh = result("05_cohort_retention")
        piv = coh.pivot(index="years_since_first", columns="cohort", values="retention_pct")
        piv.index.name = "Years since first purchase"
        st.line_chart(piv, height=280, y_label="Retention (%)")

with tab_q:
    key = st.selectbox("Question", list(labels), format_func=lambda s: labels[s])
    df = result(key)
    left, right = st.columns([1, 1.2], gap="large")
    with left:
        st.markdown("**SQL**")
        st.code((ROOT / "sql" / f"{key}.sql").read_text(), language="sql")
    with right:
        charts = {
            "01_monthly_revenue": lambda: st.line_chart(df, x="month", y=["revenue", "revenue_3mo_avg"], height=300),
            "02_country_performance": lambda: st.bar_chart(df.head(12), x="country", y="revenue", sort="-revenue", height=300),
            "03_genre_share": lambda: st.line_chart(df, x="genre", y="cumulative_pct", height=300, y_label="Cumulative share (%)"),
            "04_rfm_segments": lambda: st.scatter_chart(df, x="recency_days", y="monetary", color="segment", size="frequency", height=320),
            "05_cohort_retention": lambda: st.line_chart(df, x="years_since_first", y="retention_pct", color="cohort", height=300),
            "06_sales_reps": lambda: st.bar_chart(df, x="rep", y="revenue", sort="-revenue", height=300),
            "07_top_artist_by_country": lambda: st.bar_chart(df.head(15), x="country", y="tracks_sold", color="artist", height=320),
        }
        if key in charts:
            charts[key]()
        st.markdown(f"**Result** ({len(df)} rows)")
        st.dataframe(df, width="stretch", hide_index=True, height=300)
        st.download_button("Download CSV", df.to_csv(index=False).encode(), f"{key}.csv", "text/csv")

with tab_sql:
    st.subheader("Query the database yourself")
    st.caption(f"Read-only. One SELECT (or WITH) statement, up to {MAX_ROWS:,} rows, 3-second limit.")
    examples = {
        "Best-selling tracks": "select t.Name as track, ar.Name as artist, count(*) as sold\nfrom InvoiceLine il\njoin Track t on t.TrackId = il.TrackId\njoin Album al on al.AlbumId = t.AlbumId\njoin Artist ar on ar.ArtistId = al.ArtistId\ngroup by t.TrackId\norder by sold desc\nlimit 10",
        "Revenue by year": "select strftime('%Y', InvoiceDate) as year, round(sum(Total), 2) as revenue\nfrom Invoice\ngroup by year\norder by year",
        "Customers per country": "select Country, count(*) as customers\nfrom Customer\ngroup by Country\norder by customers desc",
        "Longest tracks": "select Name, round(Milliseconds / 60000.0, 1) as minutes\nfrom Track\norder by Milliseconds desc\nlimit 10",
    }
    left, right = st.columns([2.2, 1], gap="large")
    with right:
        st.markdown("**Examples**")
        for name, sql in examples.items():
            if st.button(name, width="stretch"):
                st.session_state["sql"] = sql
        st.markdown("**Schema**")
        for table, cols in schema().items():
            with st.expander(table):
                st.markdown("\n".join(f"- `{c}` {t.lower()}" for c, t in cols))
    with left:
        sql = st.text_area("SQL", key="sql", height=220, value=st.session_state.get("sql", examples["Best-selling tracks"]), label_visibility="collapsed")
        if st.button("Run query", type="primary"):
            try:
                out, secs, truncated = run(sql)
                st.success(f"{len(out):,} rows in {secs * 1000:.0f} ms" + (f" (first {MAX_ROWS:,} shown)" if truncated else ""))
                st.dataframe(out, width="stretch", hide_index=True)
                num = out.select_dtypes("number").columns
                if len(out) > 1 and len(num) and len(out.columns) >= 2 and out.columns[0] not in num:
                    st.bar_chart(out.head(30), x=out.columns[0], y=list(num[:2]), height=280)
                st.download_button("Download CSV", out.to_csv(index=False).encode(), "query.csv", "text/csv")
            except QueryError as e:
                st.error(str(e))

st.divider()
st.markdown(
    "Results are produced by `python analysis.py`, which also writes the full "
    "[REPORT.md](https://github.com/Aymikun19/music-store-sql-analytics/blob/main/REPORT.md)."
)
