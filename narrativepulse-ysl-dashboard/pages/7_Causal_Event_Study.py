import streamlit as st
import pandas as pd
from src.load_data import load_entity_timeseries, load_trial_events
from src.causal import simple_event_study, create_event_windows, difference_in_differences, fit_did_ols, interrupted_time_series, caveat_text
from src.plotting import event_study_plot, did_plot

st.set_page_config(page_title="Causal Event Study", layout="wide")
st.title("Causal Event Study")
st.info(caveat_text())
ts = load_entity_timeseries()
events = load_trial_events()
event = st.sidebar.selectbox("Event", events["event_name"])
event_date = events.loc[events["event_name"] == event, "date"].iloc[0]
entity = st.sidebar.selectbox("Treatment entity", sorted(ts["entity"].dropna().unique()))
control = st.sidebar.selectbox("Control entity", [e for e in sorted(ts["entity"].dropna().unique()) if e != entity])
platform = st.sidebar.selectbox("Platform", ["all"] + sorted(ts["platform"].dropna().unique()))
outcome = st.sidebar.selectbox("Outcome", ["mean_sentiment", "n_posts", "mean_engagement", "total_engagement", "positive_share", "negative_share", "neutral_share"])
window = st.sidebar.select_slider("Window", options=[1, 3, 7, 14, 30], value=14)
df = ts if platform == "all" else ts[ts["platform"] == platform]
treat_df = df[df["entity"] == entity]

st.subheader("Simple Pre/Post Event Study")
result = simple_event_study(treat_df, event_date, outcome, window)
st.dataframe(pd.DataFrame([result]), use_container_width=True, hide_index=True)
st.plotly_chart(event_study_plot(create_event_windows(treat_df, event_date, window), outcome), use_container_width=True)

st.subheader("Difference-in-Differences")
did = difference_in_differences(df, event_date, entity, control, "entity", outcome, window)
st.write({k: v for k, v in did.items() if k != "table"})
st.plotly_chart(did_plot(did["table"]), use_container_width=True)
model = fit_did_ols(df, event_date, entity, control, "entity", outcome, window)
st.text(model.summary().as_text()[:4000] if model is not None else "Not enough data to fit DiD OLS.")

st.subheader("Interrupted Time Series")
its_model, fitted = interrupted_time_series(treat_df, event_date, outcome)
if its_model is not None:
    st.text(its_model.summary().as_text()[:4000])
    st.line_chart(fitted, x="date", y=[outcome, "fitted"])
else:
    st.write("Not enough data for interrupted time-series model.")
