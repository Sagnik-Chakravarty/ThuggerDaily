import streamlit as st
from src.config import APP_TITLE, CAUSAL_CAVEAT
from src.load_data import load_posts, load_thuggerdaily_posts, load_trial_events
from src.sentiment import aggregate_sentiment_timeseries
from src.plotting import line_sentiment_over_time, line_volume_over_time, bar_records_by_platform, heatmap_platform_entity_sentiment
from src.ui_components import render_sidebar_filters, apply_filters, render_kpi_cards, render_caveat_box

st.set_page_config(page_title="NarrativePulse", layout="wide", initial_sidebar_state="expanded")
st.title(APP_TITLE)
st.caption("Legal-media intelligence and public narrative analytics for event-linked discourse measurement.")

posts = load_posts()
td = load_thuggerdaily_posts()
events = load_trial_events()
filters = render_sidebar_filters(posts)
filtered = apply_filters(posts, filters)

render_caveat_box(CAUSAL_CAVEAT)

date_min = filtered["date"].min().date() if not filtered.empty else posts["date"].min().date()
date_max = filtered["date"].max().date() if not filtered.empty else posts["date"].max().date()
render_kpi_cards(
    [
        ("Records", f"{len(filtered):,}", "Filtered records; full project analyzed 2M+ records."),
        ("Platforms", filtered["platform"].nunique(), "Distinct source platforms in current view."),
        ("Date Range", f"{date_min} to {date_max}", "Coverage in current view."),
        ("Legal Events", len(events), "Major timeline markers."),
        ("Topics", filtered["topic_label"].nunique(), "Generalized topic groups."),
        ("ThuggerDaily Posts", f"{len(td):,}", "Exposure/treatment-style records."),
        ("Entities", filtered["entity"].nunique(), "Tracked public figures/entities."),
    ]
)

st.subheader("Executive Summary")
st.write(
    "NarrativePulse demonstrates cross-platform public narrative measurement across social media, video, search, "
    "music, newspapers, magazines, and local news. The app tracks sentiment, engagement, topic prevalence, and "
    "event-linked discourse shifts around Young Thug, Gunna, and YFN Lucci. Outputs are framed as observational "
    "influence signals and platform-level public reaction, not definitive causal claims."
)

ts = aggregate_sentiment_timeseries(filtered) if not filtered.empty else aggregate_sentiment_timeseries(posts)
col1, col2 = st.columns(2)
col1.plotly_chart(line_volume_over_time(ts), use_container_width=True)
col2.plotly_chart(line_sentiment_over_time(ts), use_container_width=True)
col3, col4 = st.columns(2)
col3.plotly_chart(bar_records_by_platform(filtered), use_container_width=True)
col4.plotly_chart(heatmap_platform_entity_sentiment(filtered), use_container_width=True)
