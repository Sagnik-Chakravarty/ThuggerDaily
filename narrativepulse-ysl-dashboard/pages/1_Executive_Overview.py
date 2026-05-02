import streamlit as st
from src.config import APP_TITLE, CAUSAL_CAVEAT
from src.load_data import load_posts, load_thuggerdaily_posts, load_trial_events
from src.sentiment import aggregate_sentiment_timeseries
from src.plotting import line_sentiment_over_time, line_volume_over_time, bar_records_by_platform, heatmap_platform_entity_sentiment
from src.ui_components import render_sidebar_filters, apply_filters, render_kpi_cards, render_caveat_box

st.set_page_config(page_title="Executive Overview", layout="wide")
st.title(APP_TITLE)
st.caption("Recruiter-facing overview of legal-media intelligence and public narrative analytics.")
posts = load_posts()
td = load_thuggerdaily_posts()
events = load_trial_events()
filters = render_sidebar_filters(posts)
filtered = apply_filters(posts, filters)
render_caveat_box(CAUSAL_CAVEAT)
render_kpi_cards(
    [
        ("Records", f"{len(filtered):,}", "Filtered records; full project analyzed 2M+ records."),
        ("Platforms", filtered["platform"].nunique(), "Distinct source platforms."),
        ("Date Range", f"{filtered['date'].min().date()} to {filtered['date'].max().date()}", "Coverage in view."),
        ("Legal Events", len(events), "Major event markers."),
        ("Topics", filtered["topic_label"].nunique(), "Generalized topics."),
        ("ThuggerDaily Posts", f"{len(td):,}", "Exposure/treatment-style records."),
        ("Entities", filtered["entity"].nunique(), "Tracked entities."),
    ]
)
st.write(
    "This dashboard demonstrates cross-platform public narrative measurement, sentiment analytics, topic modeling, "
    "observational causal inference, and local-LLM reporting around the YSL RICO trial public timeline."
)
ts = aggregate_sentiment_timeseries(filtered)
col1, col2 = st.columns(2)
col1.plotly_chart(line_volume_over_time(ts), use_container_width=True)
col2.plotly_chart(line_sentiment_over_time(ts), use_container_width=True)
col3, col4 = st.columns(2)
col3.plotly_chart(bar_records_by_platform(filtered), use_container_width=True)
col4.plotly_chart(heatmap_platform_entity_sentiment(filtered), use_container_width=True)
