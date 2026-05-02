import pandas as pd
import streamlit as st
from . import demo_data
from .config import PROCESSED_DIR
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
        st.info(f"Using demo data because data/processed/{filename} was not found.")
        df = demo_data.create_demo_all()[demo_key]
    return df


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
    return _finish_posts(_read_csv_or_demo("posts_master.csv", "posts_master", ["post_id", "platform", "date", "entity"]))


@st.cache_data(show_spinner=False)
def load_thuggerdaily_posts() -> pd.DataFrame:
    return _finish_posts(_read_csv_or_demo("thuggerdaily_posts.csv", "thuggerdaily_posts", ["post_id", "date", "entity"]))


@st.cache_data(show_spinner=False)
def load_trial_events() -> pd.DataFrame:
    df = _read_csv_or_demo("trial_events.csv", "trial_events", ["event_id", "date", "event_name", "event_type", "entity"])
    return standardize_dates(df)


@st.cache_data(show_spinner=False)
def load_topic_assignments() -> pd.DataFrame:
    df = _read_csv_or_demo("topic_assignments.csv", "topic_assignments", ["post_id", "date", "platform", "entity", "topic_label"])
    return assign_topic_levels(standardize_dates(df))


@st.cache_data(show_spinner=False)
def load_entity_timeseries() -> pd.DataFrame:
    return standardize_dates(_read_csv_or_demo("entity_timeseries.csv", "entity_timeseries", ["date", "platform", "entity", "n_posts", "mean_sentiment"]))


@st.cache_data(show_spinner=False)
def load_platform_summary() -> pd.DataFrame:
    return _read_csv_or_demo("platform_summary.csv", "platform_summary", ["platform", "n_records", "min_date", "max_date"])


def load_or_create_demo_data() -> dict[str, pd.DataFrame]:
    return {
        "posts": load_posts(),
        "thuggerdaily_posts": load_thuggerdaily_posts(),
        "trial_events": load_trial_events(),
        "topic_assignments": load_topic_assignments(),
        "entity_timeseries": load_entity_timeseries(),
        "platform_summary": load_platform_summary(),
    }
