import streamlit as st
import pandas as pd
from src.load_data import load_posts, load_trial_events, load_entity_timeseries
from src.statistics import descriptive_summary, missingness_summary, duplicate_summary, pre_post_summary, mann_whitney_test, topic_distribution_shift_test, lag_correlation, regression_sentiment_ols, regression_positive_logit, regression_volume_poisson

st.set_page_config(page_title="Statistical Inference", layout="wide")
st.title("Statistical Inference")
st.info("Statistical outputs are descriptive or exploratory. They include sample size and uncertainty where feasible.")
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
st.dataframe(descriptive_summary(df), use_container_width=True, hide_index=True)
st.write(duplicate_summary(df))
st.dataframe(missingness_summary(df).head(30), use_container_width=True, hide_index=True)

st.subheader("Pre/Post Event Test")
summary = pre_post_summary(df, event_date, outcome, window)
st.dataframe(pd.DataFrame([summary]), use_container_width=True, hide_index=True)
pre = df[df["date"].between(pd.to_datetime(event_date) - pd.Timedelta(days=window), pd.to_datetime(event_date) - pd.Timedelta(days=1))][outcome]
post = df[df["date"].between(pd.to_datetime(event_date), pd.to_datetime(event_date) + pd.Timedelta(days=window))][outcome]
st.write("Mann-Whitney U:", mann_whitney_test(pre, post))

st.subheader("Topic Distribution Shift")
topic_result = topic_distribution_shift_test(df, event_date, window)
st.write({k: v for k, v in topic_result.items() if k != "table"})
if "table" in topic_result:
    st.dataframe(topic_result["table"], use_container_width=True)

st.subheader("Lag and Regression")
td_daily = df[df["author"].eq("ThuggerDaily")].groupby("date").size().reset_index(name="n_posts")
out_daily = df.groupby("date").size().reset_index(name="n_posts")
st.dataframe(lag_correlation(td_daily if not td_daily.empty else out_daily, out_daily), use_container_width=True, hide_index=True)
for name, model in [("OLS sentiment", regression_sentiment_ols(df)), ("Logit positive", regression_positive_logit(df)), ("Poisson volume", regression_volume_poisson(entity_ts))]:
    st.markdown(f"#### {name}")
    st.text(model.summary().as_text()[:4000] if model is not None else "Not enough variation or observations to fit this model.")
