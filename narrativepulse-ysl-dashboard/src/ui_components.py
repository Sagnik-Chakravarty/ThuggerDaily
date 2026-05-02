import streamlit as st
from .config import CAUSAL_CAVEAT


def render_sidebar_filters(posts):
    st.sidebar.header("Filters")
    entities = ["all"] + sorted([x for x in posts["entity"].dropna().unique()])
    platforms = ["all"] + sorted([x for x in posts["platform"].dropna().unique()])
    entity = st.sidebar.selectbox("Entity", entities)
    platform = st.sidebar.selectbox("Platform", platforms)
    min_date = posts["date"].min().date()
    max_date = posts["date"].max().date()
    date_range = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)
    return {"entity": entity, "platform": platform, "date_range": date_range}


def apply_filters(posts, filters):
    df = posts.copy()
    if filters.get("entity") != "all":
        df = df[df["entity"] == filters["entity"]]
    if filters.get("platform") != "all":
        df = df[df["platform"] == filters["platform"]]
    date_range = filters.get("date_range")
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[df["date"].dt.date.between(start, end)]
    return df


def render_kpi_cards(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)


def render_caveat_box(text=CAUSAL_CAVEAT):
    st.info(text)


def render_data_warning(message):
    st.warning(message)


def render_methodology_note():
    st.caption("Methods are designed for aggregate, processed, public, sampled, or anonymized data. Interpret outputs as public narrative signals.")
