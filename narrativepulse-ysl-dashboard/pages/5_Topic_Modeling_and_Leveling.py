import streamlit as st
from src.load_data import load_posts, load_topic_assignments, load_trial_events
from src.topic_modeling import aggregate_topic_prevalence, topic_prevalence_over_time, top_words_by_topic, representative_posts_by_topic, topic_shift_pre_post, topic_entropy_over_time
from src.topic_leveling import topic_level_summary
from src.plotting import topic_prevalence_area, topic_heatmap
from src.ui_components import apply_light_theme

st.set_page_config(page_title="Topic Modeling", layout="wide")
apply_light_theme()
st.title("Topic Modeling and Topic Leveling")
posts = load_posts()
topics = load_topic_assignments()
events = load_trial_events()

st.subheader("Seven Generalized Topic Groups")
st.dataframe(topic_level_summary(posts), use_container_width=True, hide_index=True)
prev = topic_prevalence_over_time(posts)
st.plotly_chart(topic_prevalence_area(prev.groupby(["date", "topic_label"])["topic_share"].mean().reset_index()), use_container_width=True)
col1, col2 = st.columns(2)
col1.plotly_chart(topic_heatmap(aggregate_topic_prevalence(posts, ["platform", "topic_label"])), use_container_width=True)
col2.line_chart(topic_entropy_over_time(posts), x="date", y="topic_entropy")

st.subheader("Top Words and Representative Posts")
st.dataframe(top_words_by_topic(topics), use_container_width=True, hide_index=True)
st.dataframe(representative_posts_by_topic(posts)[["date", "platform", "entity", "topic_label", "text"]], use_container_width=True, hide_index=True)

event_name = st.selectbox("Topic shift around event", events["event_name"])
event_date = events.loc[events["event_name"] == event_name, "date"].iloc[0]
st.dataframe(topic_shift_pre_post(posts, event_date), use_container_width=True, hide_index=True)
