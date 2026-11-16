"""Streamlit explorer for the SQL analysis.  Run with:  streamlit run app.py"""
from pathlib import Path

import pandas as pd
import streamlit as st

ROOT = Path(__file__).parent
st.set_page_config(page_title="Music Store SQL Analytics", page_icon="🎵", layout="wide")
st.title("🎵 Music Store SQL Analytics")
st.caption(
    "Seven business questions answered in SQL on the Chinook store database. "
    "Pick a question to see the query, its result and the chart."
)

queries = sorted((ROOT / "sql").glob("*.sql"))
labels = {q.stem: q.read_text().splitlines()[0].lstrip("- ").strip() for q in queries}
figures = {
    "01_monthly_revenue": "monthly_revenue",
    "03_genre_share": "genre_pareto",
    "04_rfm_segments": "rfm_segments",
    "05_cohort_retention": "cohort_retention",
}

key = st.radio("Question", list(labels), format_func=lambda k: labels[k], label_visibility="collapsed")
df = pd.read_csv(ROOT / "results" / f"{key}.csv")

left, right = st.columns([1, 1])
with left:
    st.subheader("SQL")
    st.code((ROOT / "sql" / f"{key}.sql").read_text(), language="sql")
with right:
    if key in figures:
        st.subheader("Chart")
        st.image(str(ROOT / "figures" / f"{figures[key]}.png"), width="stretch")
    st.subheader(f"Result ({len(df)} rows)")
    st.dataframe(df, width="stretch", hide_index=True)

st.divider()
st.markdown(
    "Results are produced by `python analysis.py`, which also writes the full "
    "[REPORT.md](https://github.com/Aymikun19/music-store-sql-analytics/blob/main/REPORT.md)."
)
