import streamlit as st
import pandas as pd
from src.load_data import load_posts, load_trial_events, load_entity_timeseries
from src.statistics import descriptive_summary, missingness_summary, duplicate_summary, pre_post_summary, mann_whitney_test, topic_distribution_shift_test, lag_correlation, regression_sentiment_ols, regression_positive_logit, regression_volume_poisson
from src.ui_components import apply_light_theme, render_model_summary

st.set_page_config(page_title="Statistical Inference", layout="wide")
apply_light_theme()
st.title("Statistical Inference")
st.caption("Descriptive and exploratory statistical outputs with sample sizes, estimates, uncertainty, and interpretation.")
posts = load_posts()
events = load_trial_events()
entity_ts = load_entity_timeseries()

entity = st.sidebar.selectbox("Entity", ["all"] + sorted(posts["entity"].dropna().unique()))
platform = st.sidebar.selectbox("Platform", ["all"] + sorted(posts["platform"].dropna().unique()))
event = st.sidebar.selectbox("Event", events["event_name"])
window = st.sidebar.select_slider("Window", options=[1, 3, 7, 14, 30], value=7)
outcome = st.sidebar.selectbox("Outcome", ["sentiment_score", "total_engagement", "engagement_rate"])
df = posts.copy()
if entity != "all":
    df = df[df["entity"] == entity]
if platform != "all":
    df = df[df["platform"] == platform]
event_date = events.loc[events["event_name"] == event, "date"].iloc[0]

st.subheader("Descriptive Statistics")
dupes = duplicate_summary(df)
k1, k2, k3 = st.columns(3)
k1.metric("Rows in Scope", f"{dupes['n_rows']:,}")
k2.metric("Duplicate Post IDs", f"{dupes['n_duplicate_rows']:,}")
k3.metric("Platforms", df["platform"].nunique())
st.dataframe(descriptive_summary(df).round(4), use_container_width=True, hide_index=True)
with st.expander("Missingness by field"):
    st.dataframe(missingness_summary(df).head(30).round(3), use_container_width=True, hide_index=True)

st.subheader("Pre/Post Event Test")
summary = pre_post_summary(df, event_date, outcome, window)
metric_cols = st.columns(5)
metric_cols[0].metric("Pre Mean", f"{summary['pre_mean']:.3f}" if pd.notna(summary["pre_mean"]) else "n/a")
metric_cols[1].metric("Post Mean", f"{summary['post_mean']:.3f}" if pd.notna(summary["post_mean"]) else "n/a")
metric_cols[2].metric("Difference", f"{summary['difference']:.3f}" if pd.notna(summary["difference"]) else "n/a")
metric_cols[3].metric("p-value", f"{summary['p_value']:.3f}" if pd.notna(summary["p_value"]) else "n/a")
metric_cols[4].metric("Effect Size", f"{summary['effect_size']:.3f}" if pd.notna(summary["effect_size"]) else "n/a")
st.caption(f"Window: {window} days before vs. {window} days after. Sample sizes: pre={summary['pre_n']}, post={summary['post_n']}.")
pre = df[df["date"].between(pd.to_datetime(event_date) - pd.Timedelta(days=window), pd.to_datetime(event_date) - pd.Timedelta(days=1))][outcome]
post = df[df["date"].between(pd.to_datetime(event_date), pd.to_datetime(event_date) + pd.Timedelta(days=window))][outcome]
mw = mann_whitney_test(pre, post)
st.dataframe(pd.DataFrame([{
    "test": "Mann-Whitney U",
    "statistic": mw["statistic"],
    "p_value": mw["p_value"],
    "interpretation": "Nonparametric pre/post comparison; exploratory, not causal proof.",
}]).round(4), use_container_width=True, hide_index=True)

st.subheader("Topic Distribution Shift")
topic_result = topic_distribution_shift_test(df, event_date, window)
topic_summary = {k: v for k, v in topic_result.items() if k != "table"}
st.dataframe(pd.DataFrame([topic_summary]).round(4), use_container_width=True, hide_index=True)
if "table" in topic_result:
    with st.expander("Topic pre/post count table"):
        st.dataframe(topic_result["table"], use_container_width=True)

st.subheader("Lag and Regression")
td_daily = df[df["author"].eq("ThuggerDaily")].groupby("date").size().reset_index(name="n_posts")
out_daily = df.groupby("date").size().reset_index(name="n_posts")
st.dataframe(lag_correlation(td_daily if not td_daily.empty else out_daily, out_daily), use_container_width=True, hide_index=True)
render_model_summary(regression_sentiment_ols(df), "OLS sentiment model")
render_model_summary(regression_positive_logit(df), "Positive sentiment logistic model")
render_model_summary(regression_volume_poisson(entity_ts), "Poisson volume model")
