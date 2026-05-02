import pandas as pd
import streamlit as st
from . import demo_data
from .config import PROCESSED_DIR
from .database import database_available, read_table
from .engagement import calculate_engagement_rate, calculate_total_engagement
from .preprocessing import ensure_required_columns, standardize_dates, standardize_entity_names, standardize_platform_names
from .topic_leveling import assign_topic_levels

POST_COLUMNS = [
    "post_id", "platform", "date", "text", "author", "entity", "sentiment_score", "sentiment_label",
    "likes", "comments", "shares", "retweets", "views", "analytics", "engagement_rate", "topic_id",
    "topic_label", "topic_level_1", "topic_level_2", "topic_level_3", "url",
]


def validate_schema(df: pd.DataFrame, required: list[str]) -> tuple[bool, list[str]]:
    missing = [c for c in required if c not in df.columns]
    return len(missing) == 0, missing


def _read_csv_or_demo(filename: str, demo_key: str, required: list[str]) -> pd.DataFrame:
    path = PROCESSED_DIR / filename
    if path.exists():
        df = pd.read_csv(path)
        ok, missing = validate_schema(df, required)
        if not ok:
            st.warning(f"{filename} is missing columns: {', '.join(missing)}. Placeholder columns were added where possible.")
            df = ensure_required_columns(df, required)
    else:
        df = demo_data.create_demo_all()[demo_key]
    return df


def _read_database_or_csv(table_name: str, filename: str, demo_key: str, required: list[str], parse_dates=None) -> pd.DataFrame:
    if database_available():
        try:
            df = read_table(table_name, parse_dates=parse_dates)
            ok, missing = validate_schema(df, required)
            if not ok:
                st.warning(f"Database table {table_name} is missing columns: {', '.join(missing)}.")
                df = ensure_required_columns(df, required)
            return df
        except Exception as exc:
            st.warning(f"Database read failed for {table_name}; falling back to local CSV/demo data. Details: {exc}")
    return _read_csv_or_demo(filename, demo_key, required)


def missing_processed_files(filenames=None) -> list[str]:
    if database_available():
        return []
    filenames = filenames or [
        "posts_master.csv",
        "thuggerdaily_posts.csv",
        "trial_events.csv",
        "topic_assignments.csv",
        "entity_timeseries.csv",
        "platform_summary.csv",
    ]
    return [name for name in filenames if not (PROCESSED_DIR / name).exists()]


def _finish_posts(df: pd.DataFrame) -> pd.DataFrame:
    df = standardize_dates(standardize_entity_names(standardize_platform_names(df)))
    df = ensure_required_columns(df, POST_COLUMNS)
    df = assign_topic_levels(df)
    if "total_engagement" not in df:
        df["total_engagement"] = calculate_total_engagement(df)
    if df["engagement_rate"].isna().all():
        df["engagement_rate"] = calculate_engagement_rate(df)
    return df


@st.cache_data(show_spinner=False)
def load_posts() -> pd.DataFrame:
    return _finish_posts(_read_database_or_csv("posts_master", "posts_master.csv", "posts_master", ["post_id", "platform", "date", "entity"], parse_dates=["date"]))


@st.cache_data(show_spinner=False)
def load_thuggerdaily_posts() -> pd.DataFrame:
    return _finish_posts(_read_database_or_csv("thuggerdaily_posts", "thuggerdaily_posts.csv", "thuggerdaily_posts", ["post_id", "date", "entity"], parse_dates=["date"]))


@st.cache_data(show_spinner=False)
def load_trial_events() -> pd.DataFrame:
    df = _read_database_or_csv("trial_events", "trial_events.csv", "trial_events", ["event_id", "date", "event_name", "event_type", "entity"], parse_dates=["date"])
    return standardize_dates(df)


@st.cache_data(show_spinner=False)
def load_topic_assignments() -> pd.DataFrame:
    df = _read_database_or_csv("topic_assignments", "topic_assignments.csv", "topic_assignments", ["post_id", "date", "platform", "entity", "topic_label"], parse_dates=["date"])
    return assign_topic_levels(standardize_dates(df))


@st.cache_data(show_spinner=False)
def load_entity_timeseries() -> pd.DataFrame:
    return standardize_dates(_read_database_or_csv("entity_timeseries", "entity_timeseries.csv", "entity_timeseries", ["date", "platform", "entity", "n_posts", "mean_sentiment"], parse_dates=["date"]))


@st.cache_data(show_spinner=False)
def load_platform_summary() -> pd.DataFrame:
    return _read_database_or_csv("platform_summary", "platform_summary.csv", "platform_summary", ["platform", "n_records", "min_date", "max_date"], parse_dates=["min_date", "max_date"])


def load_or_create_demo_data() -> dict[str, pd.DataFrame]:
    return {
        "posts": load_posts(),
        "thuggerdaily_posts": load_thuggerdaily_posts(),
        "trial_events": load_trial_events(),
        "topic_assignments": load_topic_assignments(),
        "entity_timeseries": load_entity_timeseries(),
        "platform_summary": load_platform_summary(),
    }
