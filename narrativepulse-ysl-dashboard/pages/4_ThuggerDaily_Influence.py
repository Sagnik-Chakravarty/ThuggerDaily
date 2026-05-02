import streamlit as st
import pandas as pd
from src.load_data import load_posts, load_thuggerdaily_posts
from src.statistics import pre_post_summary, lag_correlation
from src.sentiment import aggregate_sentiment_timeseries
from src.plotting import engagement_spike_plot, line_volume_over_time, line_sentiment_over_time, lag_correlation_plot
from src.ui_components import apply_light_theme, render_caveat_box

st.set_page_config(page_title="ThuggerDaily Influence", layout="wide")
apply_light_theme()
st.title("ThuggerDaily Influence Signals")
render_caveat_box("This module estimates temporal association around observed posts. It does not prove randomized causal effects.")

posts = load_posts()
td = load_thuggerdaily_posts()
window = st.sidebar.select_slider("Pre/post window", options=[1, 3, 7, 14, 30], value=7)
entity = st.sidebar.selectbox("Entity", ["all"] + sorted(posts["entity"].dropna().unique()))
public = posts if entity == "all" else posts[posts["entity"] == entity]
td_view = td if entity == "all" else td[td["entity"] == entity]

daily_td = td_view.groupby("date").agg(n_posts=("post_id", "count"), total_engagement=("total_engagement", "sum"), mean_sentiment=("sentiment_score", "mean")).reset_index()
public_ts = aggregate_sentiment_timeseries(public)

col1, col2 = st.columns(2)
col1.plotly_chart(engagement_spike_plot(td_view), use_container_width=True)
col2.plotly_chart(line_volume_over_time(public_ts), use_container_width=True)
st.plotly_chart(line_sentiment_over_time(public_ts), use_container_width=True)

rows = []
for _, post in td_view.sort_values("total_engagement", ascending=False).head(25).iterrows():
    sentiment = pre_post_summary(public, post["date"], "sentiment_score", window)
    volume_daily = public.groupby("date").size().reset_index(name="volume")
    volume = pre_post_summary(volume_daily, post["date"], "volume", window)
    rows.append({
        "post_id": post["post_id"], "date": post["date"], "entity": post["entity"], "topic_label": post["topic_label"],
        "td_engagement": post["total_engagement"], "sentiment_diff": sentiment["difference"], "volume_diff": volume["difference"],
        "sentiment_p_value": sentiment["p_value"],
    })
influence = pd.DataFrame(rows)
st.subheader("Most Influential Demo Posts by Downstream Shift")
st.dataframe(influence.sort_values("volume_diff", ascending=False), use_container_width=True, hide_index=True)

lag_df = lag_correlation(daily_td, public_ts.groupby("date").agg(n_posts=("n_posts", "sum"), mean_sentiment=("mean_sentiment", "mean")).reset_index(), "n_posts", "n_posts")
st.plotly_chart(lag_correlation_plot(lag_df), use_container_width=True)
