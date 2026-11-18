"""Read-only SQL runner for the Streamlit playground.

Safety: the database is opened read-only through SQLite's URI mode, only a single SELECT/WITH statement
is accepted, the authorizer rejects anything that writes or attaches, and a progress handler stops
runaway queries.
"""
from __future__ import annotations

import re
import sqlite3
import time
from pathlib import Path

import pandas as pd

DB = Path(__file__).parent / "data" / "chinook.sqlite"
MAX_ROWS = 5000
TIME_LIMIT = 3.0

_ALLOWED = {sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ, sqlite3.SQLITE_FUNCTION}


class QueryError(ValueError):
    pass


def _strip_comments(sql: str) -> str:
    sql = re.sub(r"/\*.*?\*/", " ", sql, flags=re.S)
    return re.sub(r"--[^\n]*", " ", sql)


def validate(sql: str) -> str:
    body = _strip_comments(sql).strip().rstrip(";").strip()
    if not body:
        raise QueryError("Write a query first.")
    if ";" in body:
        raise QueryError("Run one statement at a time.")
    if not re.match(r"(?is)^(select|with)\b", body):
        raise QueryError("Only SELECT queries (optionally starting with WITH) are allowed.")
    return body


def run(sql: str, db: Path = DB) -> tuple[pd.DataFrame, float, bool]:
    """Returns (rows, seconds, truncated)."""
    body = validate(sql)
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        con.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in _ALLOWED else sqlite3.SQLITE_DENY)
        start = time.perf_counter()
        con.set_progress_handler(lambda: 1 if time.perf_counter() - start > TIME_LIMIT else 0, 10_000)
        try:
            cur = con.execute(body)
            rows = cur.fetchmany(MAX_ROWS + 1)
        except sqlite3.DatabaseError as e:
            msg = str(e)
            if "interrupted" in msg:
                msg = f"The query took longer than {TIME_LIMIT:.0f} seconds and was stopped."
            elif "not authorized" in msg:
                msg = "That query tries to do something other than read data."
            raise QueryError(msg) from None
        cols = [d[0] for d in cur.description or []]
        truncated = len(rows) > MAX_ROWS
        return pd.DataFrame(rows[:MAX_ROWS], columns=cols), time.perf_counter() - start, truncated
    finally:
        con.close()


def schema(db: Path = DB) -> dict[str, list[tuple[str, str]]]:
    con = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
    try:
        tables = [r[0] for r in con.execute("select name from sqlite_master where type='table' order by name")]
        return {t: [(c[1], c[2]) for c in con.execute(f'pragma table_info("{t}")')] for t in tables}
    finally:
        con.close()


def encode_share(sql: str) -> str:
    """Compact, URL-safe token for a query, used in ?q= share links."""
    import base64
    import zlib

    return base64.urlsafe_b64encode(zlib.compress(sql.strip().encode(), 9)).decode().rstrip("=")


def decode_share(token: str, max_len: int = 10_000) -> str | None:
    """Inverse of encode_share; returns None for anything malformed or oversized."""
    import base64
    import binascii
    import zlib

    try:
        raw = base64.urlsafe_b64decode(token + "=" * (-len(token) % 4))
        d = zlib.decompressobj()
        out = d.decompress(raw, max_len + 1)
        if len(out) > max_len or d.unconsumed_tail:
            return None
        return out.decode()
    except (binascii.Error, zlib.error, UnicodeDecodeError, ValueError):
        return None
