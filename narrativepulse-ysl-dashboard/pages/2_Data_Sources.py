import streamlit as st
from src.load_data import load_posts, load_platform_summary
from src.plotting import bar_records_by_platform, missingness_heatmap
from src.ui_components import apply_light_theme, render_caveat_box

st.set_page_config(page_title="Data Sources", layout="wide")
apply_light_theme()
st.title("Data Sources")
render_caveat_box("Coverage reflects available public, processed, sampled, or demo records. API and scraping constraints can introduce platform bias.")

posts = load_posts()
summary = load_platform_summary()
st.subheader("Source Coverage")
st.dataframe(summary, use_container_width=True, hide_index=True)

col1, col2 = st.columns(2)
col1.plotly_chart(bar_records_by_platform(summary), use_container_width=True)
col2.plotly_chart(missingness_heatmap(posts), use_container_width=True)

st.subheader("Coverage Timeline")
coverage = posts.groupby(["platform", posts["date"].dt.to_period("M").dt.to_timestamp()]).size().reset_index(name="records")
st.bar_chart(coverage, x="date", y="records", color="platform")

st.markdown(
    "Sources include social media, video, search, music, newspapers, magazines, and local news. "
    "Available fields differ by platform; missing denominators use raw engagement counts where engagement rates cannot be computed."
)
