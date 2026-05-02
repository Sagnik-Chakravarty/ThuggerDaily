import streamlit as st
import plotly.express as px
from src.load_data import load_posts
from src.sentiment import aggregate_sentiment_timeseries, smooth_sentiment, compare_sentiment_by_platform, compare_sentiment_by_entity
from src.plotting import line_sentiment_over_time, line_volume_over_time, stacked_sentiment_share, heatmap_platform_entity_sentiment
from src.ui_components import apply_light_theme, render_sidebar_filters, apply_filters

st.set_page_config(page_title="Multi-Platform Sentiment", layout="wide")
apply_light_theme()
st.title("Multi-Platform Sentiment")
posts = load_posts()
filters = render_sidebar_filters(posts)
label = st.sidebar.selectbox("Sentiment label", ["all", "positive", "negative", "neutral"])
window = st.sidebar.select_slider("Smoothing window", options=[1, 3, 7, 14, 30], value=7)
df = apply_filters(posts, filters)
if label != "all":
    df = df[df["sentiment_label"] == label]

ts = smooth_sentiment(aggregate_sentiment_timeseries(df), window=window) if not df.empty else aggregate_sentiment_timeseries(posts)
sentiment_plot = ts.copy()
if "smoothed_sentiment" in sentiment_plot:
    sentiment_plot["mean_sentiment"] = sentiment_plot["smoothed_sentiment"]
st.plotly_chart(line_sentiment_over_time(sentiment_plot), use_container_width=True)
col1, col2 = st.columns(2)
col1.plotly_chart(line_volume_over_time(ts), use_container_width=True)
col2.plotly_chart(stacked_sentiment_share(ts.groupby("date")[["positive_share", "negative_share", "neutral_share"]].mean().reset_index()), use_container_width=True)
col3, col4 = st.columns(2)
col3.plotly_chart(heatmap_platform_entity_sentiment(df), use_container_width=True)
col4.plotly_chart(px.histogram(df, x="sentiment_score", color="entity", nbins=40, template="plotly_white", title="Sentiment Score Distribution"), use_container_width=True)

st.subheader("Sentiment Summary")
c1, c2 = st.columns(2)
c1.dataframe(compare_sentiment_by_platform(df), use_container_width=True, hide_index=True)
c2.dataframe(compare_sentiment_by_entity(df), use_container_width=True, hide_index=True)
if "text" in df:
    st.subheader("Example High/Low Sentiment Posts")
    st.dataframe(df.sort_values("sentiment_score", ascending=False)[["date", "platform", "entity", "sentiment_score", "text"]].head(10), use_container_width=True, hide_index=True)
    st.dataframe(df.sort_values("sentiment_score")[["date", "platform", "entity", "sentiment_score", "text"]].head(10), use_container_width=True, hide_index=True)
