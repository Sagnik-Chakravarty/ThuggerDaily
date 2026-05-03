from __future__ import annotations

import os
from pathlib import Path
from urllib.parse import urlparse, parse_qsl, urlencode, urlunparse

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = ROOT.parent


def _read_env_file(path: Path) -> dict[str, str]:
    values = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8", errors="ignore").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip().strip('"').strip("'")
    return values


def _streamlit_secret(name: str):
    try:
        import streamlit as st

        return st.secrets.get(name)
    except Exception:
        return None


def get_database_url() -> str | None:
    keys = ["DATABASE_URL", "POSTGRES_URL", "NEON_DATABASE_URL", "NEON_DB"]
    for key in keys:
        value = os.getenv(key) or _streamlit_secret(key)
        if value:
            return str(value)
    for env_path in [ROOT / ".env", REPO_ROOT / ".env"]:
        values = _read_env_file(env_path)
        for key in keys:
            if values.get(key):
                return values[key]
    return None


def psycopg_url(url: str) -> str:
    """Drop libpq-only query args psycopg may not understand."""
    parsed = urlparse(url)
    query = dict(parse_qsl(parsed.query, keep_blank_values=True))
    allowed = {k: v for k, v in query.items() if k in {"sslmode", "connect_timeout", "application_name"}}
    return urlunparse(parsed._replace(query=urlencode(allowed)))


def read_table(table_name: str, parse_dates=None) -> pd.DataFrame:
    try:
        import psycopg
    except Exception as exc:  # pragma: no cover
        raise RuntimeError(
            "Postgres driver is not available. Install `psycopg[binary]` or disable database mode."
        ) from exc

    url = get_database_url()
    if not url:
        raise RuntimeError("DATABASE_URL is not configured.")
    with psycopg.connect(psycopg_url(url)) as conn:
        df = pd.read_sql_query(f'SELECT * FROM "{table_name}"', conn)
    for col in parse_dates or []:
        if col in df:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return df


def database_available() -> bool:
    try:
        import psycopg
    except Exception:
        return False

    url = get_database_url()
    if not url:
        return False
    try:
        with psycopg.connect(psycopg_url(url), connect_timeout=5) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return True
    except Exception:
        return False
