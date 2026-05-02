import streamlit as st
import pandas as pd
from src.load_data import load_entity_timeseries, load_trial_events, load_thuggerdaily_posts
from src.causal import simple_event_study, create_event_windows, difference_in_differences, fit_did_ols, interrupted_time_series, estimate_thuggerdaily_attribution, caveat_text
from src.plotting import event_study_plot, did_plot
from src.ui_components import apply_light_theme, render_model_summary

st.set_page_config(page_title="Causal Event Study", layout="wide")
apply_light_theme()
st.title("Causal Event Study")
st.caption("Observational event-study tools for estimating temporal association, not legal truth or randomized causal effects.")
ts = load_entity_timeseries()
events = load_trial_events()
td_posts = load_thuggerdaily_posts()
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
cols = st.columns(5)
cols[0].metric("Pre Mean", f"{result['pre_mean']:.3f}" if pd.notna(result["pre_mean"]) else "n/a")
cols[1].metric("Post Mean", f"{result['post_mean']:.3f}" if pd.notna(result["post_mean"]) else "n/a")
cols[2].metric("Observed Shift", f"{result['difference']:.3f}" if pd.notna(result["difference"]) else "n/a")
cols[3].metric("Percent Change", f"{result['percent_change']:.1f}%" if pd.notna(result["percent_change"]) else "n/a")
cols[4].metric("Effect Size", f"{result['effect_size']:.3f}" if pd.notna(result["effect_size"]) else "n/a")
st.caption(f"Sample sizes: pre={result['n_pre']}, post={result['n_post']}. {caveat_text()}")
st.plotly_chart(event_study_plot(create_event_windows(treat_df, event_date, window), outcome), use_container_width=True)

st.subheader("ThuggerDaily-Aligned Attribution Estimate")
attrib = estimate_thuggerdaily_attribution(ts, td_posts, event_date, entity, platform, outcome, window)
if "status" in attrib:
    st.warning(attrib["status"])
else:
    a_cols = st.columns(4)
    a_cols[0].metric("Observed Shift", f"{attrib['observed_shift']:.3f}" if pd.notna(attrib["observed_shift"]) else "n/a")
    a_cols[1].metric("Exposure Lift", f"{attrib['exposure_lift']:.3f}" if pd.notna(attrib["exposure_lift"]) else "n/a")
    a_cols[2].metric("Aligned Share", f"{attrib['attribution_percent']:.1f}%" if pd.notna(attrib["attribution_percent"]) else "n/a")
    a_cols[3].metric("TD Posts in Window", f"{attrib['td_posts_in_post_window']:,}")
    st.dataframe(pd.DataFrame([{
        "post_window_days": attrib["post_window_days"],
        "td_exposed_days": attrib["td_exposed_days"],
        "td_engagement_in_post_window": attrib["td_engagement_in_post_window"],
        "exposed_day_mean": attrib["exposed_day_mean"],
        "unexposed_day_mean": attrib["unexposed_day_mean"],
        "interpretation": attrib["interpretation"],
    }]).round(4), use_container_width=True, hide_index=True)

st.subheader("Difference-in-Differences")
did = difference_in_differences(df, event_date, entity, control, "entity", outcome, window)
did_cols = st.columns(3)
did_cols[0].metric("DiD Estimate", f"{did['did_estimate']:.3f}" if pd.notna(did["did_estimate"]) else "n/a")
did_cols[1].metric("Rows Used", f"{did['n']:,}")
did_cols[2].metric("Control", control)
st.caption(did["interpretation"])
st.plotly_chart(did_plot(did["table"]), use_container_width=True)
model = fit_did_ols(df, event_date, entity, control, "entity", outcome, window)
render_model_summary(model, "DiD OLS coefficient table")

st.subheader("Interrupted Time Series")
its_model, fitted = interrupted_time_series(treat_df, event_date, outcome)
if its_model is not None:
    render_model_summary(its_model, "Interrupted time-series coefficient table")
    st.line_chart(fitted, x="date", y=[outcome, "fitted"])
else:
    st.write("Not enough data for interrupted time-series model.")
