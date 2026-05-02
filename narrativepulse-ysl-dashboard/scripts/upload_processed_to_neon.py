from __future__ import annotations

import csv
from pathlib import Path
import sys

import pandas as pd
import psycopg

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.database import get_database_url, psycopg_url

DATA = ROOT / "data" / "processed"

TABLES = {
    "posts_master": DATA / "posts_master.csv",
    "thuggerdaily_posts": DATA / "thuggerdaily_posts.csv",
    "trial_events": DATA / "trial_events.csv",
    "topic_assignments": DATA / "topic_assignments.csv",
    "entity_timeseries": DATA / "entity_timeseries.csv",
    "platform_summary": DATA / "platform_summary.csv",
}

TYPE_HINTS = {
    "date": "TIMESTAMPTZ",
    "min_date": "TIMESTAMPTZ",
    "max_date": "TIMESTAMPTZ",
    "sentiment_score": "DOUBLE PRECISION",
    "likes": "DOUBLE PRECISION",
    "comments": "DOUBLE PRECISION",
    "shares": "DOUBLE PRECISION",
    "retweets": "DOUBLE PRECISION",
    "views": "DOUBLE PRECISION",
    "analytics": "DOUBLE PRECISION",
    "engagement_rate": "DOUBLE PRECISION",
    "total_engagement": "DOUBLE PRECISION",
    "mean_sentiment": "DOUBLE PRECISION",
    "positive_share": "DOUBLE PRECISION",
    "negative_share": "DOUBLE PRECISION",
    "neutral_share": "DOUBLE PRECISION",
    "mean_engagement": "DOUBLE PRECISION",
    "n_posts": "INTEGER",
    "n_records": "INTEGER",
    "topic_id": "INTEGER",
    "has_sentiment": "BOOLEAN",
    "has_topic": "BOOLEAN",
    "has_engagement": "BOOLEAN",
}


def q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def column_type(name: str) -> str:
    return TYPE_HINTS.get(name, "TEXT")


def create_table_sql(table: str, columns: list[str]) -> str:
    cols = ",\n  ".join(f"{q(col)} {column_type(col)}" for col in columns)
    return f"DROP TABLE IF EXISTS {q(table)};\nCREATE TABLE {q(table)} (\n  {cols}\n);"


def normalize_csv_for_copy(src: Path, dest: Path, columns: list[str]) -> None:
    df_iter = pd.read_csv(src, chunksize=25000, low_memory=False)
    first = True
    for chunk in df_iter:
        chunk = chunk.reindex(columns=columns)
        for col, typ in TYPE_HINTS.items():
            if col in chunk and typ == "BOOLEAN":
                chunk[col] = chunk[col].map(lambda x: "" if pd.isna(x) else str(bool(x)).lower())
        chunk.to_csv(dest, mode="w" if first else "a", header=first, index=False, quoting=csv.QUOTE_MINIMAL)
        first = False


def copy_table(conn, table: str, path: Path) -> int:
    columns = list(pd.read_csv(path, nrows=0).columns)
    with conn.cursor() as cur:
        cur.execute(create_table_sql(table, columns))
    temp = path.with_suffix(path.suffix + ".copytmp")
    normalize_csv_for_copy(path, temp, columns)
    col_sql = ", ".join(q(c) for c in columns)
    with conn.cursor() as cur:
        with temp.open("r", encoding="utf-8", newline="") as f:
            with cur.copy(f"COPY {q(table)} ({col_sql}) FROM STDIN WITH (FORMAT CSV, HEADER TRUE, NULL '')") as copy:
                while data := f.read(1024 * 1024):
                    copy.write(data)
    temp.unlink(missing_ok=True)
    with conn.cursor() as cur:
        cur.execute(f"SELECT COUNT(*) FROM {q(table)}")
        return int(cur.fetchone()[0])


def create_indexes(conn) -> None:
    indexes = [
        'CREATE INDEX IF NOT EXISTS idx_posts_master_date ON "posts_master" ("date")',
        'CREATE INDEX IF NOT EXISTS idx_posts_master_entity ON "posts_master" ("entity")',
        'CREATE INDEX IF NOT EXISTS idx_posts_master_platform ON "posts_master" ("platform")',
        'CREATE INDEX IF NOT EXISTS idx_posts_master_topic ON "posts_master" ("topic_label")',
        'CREATE INDEX IF NOT EXISTS idx_td_date ON "thuggerdaily_posts" ("date")',
        'CREATE INDEX IF NOT EXISTS idx_entity_ts_date ON "entity_timeseries" ("date")',
    ]
    with conn.cursor() as cur:
        for statement in indexes:
            cur.execute(statement)


def main():
    url = get_database_url()
    if not url:
        raise SystemExit("DATABASE_URL was not found in environment, Streamlit secrets, or .env.")
    missing = [str(path) for path in TABLES.values() if not path.exists()]
    if missing:
        raise SystemExit(f"Missing processed files: {missing}")
    with psycopg.connect(psycopg_url(url)) as conn:
        for table, path in TABLES.items():
            count = copy_table(conn, table, path)
            print(f"Uploaded {table}: {count:,} rows")
        create_indexes(conn)
        conn.commit()
    print("Neon upload complete.")


if __name__ == "__main__":
    main()
