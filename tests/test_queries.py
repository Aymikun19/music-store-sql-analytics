"""Sanity checks: the SQL results must reconcile with the raw tables."""
import sqlite3
from pathlib import Path

import pandas as pd
import pytest

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "data" / "chinook.sqlite"
pytestmark = pytest.mark.skipif(not DB.exists(), reason="run python analysis.py first to download the database")


def q(name):
    return pd.read_sql_query((ROOT / "sql" / f"{name}.sql").read_text(), sqlite3.connect(DB))


def total_revenue():
    return sqlite3.connect(DB).execute("SELECT ROUND(SUM(Total), 2) FROM Invoice").fetchone()[0]


def test_monthly_revenue_reconciles():
    assert q("01_monthly_revenue")["revenue"].sum() == pytest.approx(total_revenue(), abs=0.05)


def test_genre_shares_sum_to_100():
    g = q("03_genre_share")
    assert g["share_pct"].sum() == pytest.approx(100, abs=0.5)
    assert g["cumulative_pct"].iloc[-1] == pytest.approx(100, abs=0.1)


def test_every_customer_gets_one_segment():
    seg = q("04_rfm_segments")
    n = sqlite3.connect(DB).execute("SELECT COUNT(DISTINCT CustomerId) FROM Invoice").fetchone()[0]
    assert len(seg) == n and seg["segment"].notna().all()


def test_cohort_year_zero_is_100_pct():
    c = q("05_cohort_retention")
    assert (c.loc[c.years_since_first == 0, "retention_pct"] == 100).all()
