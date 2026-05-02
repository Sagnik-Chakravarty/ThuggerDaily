import streamlit as st
from src.load_data import load_posts, load_trial_events
from src.llm_reporting import list_ollama_models, generate_llm_report

st.set_page_config(page_title="Timeline Report Generator", layout="wide")
st.title("Timeline Report Generator")
st.caption("Uses local Ollama when available; otherwise returns a template report.")
posts = load_posts()
events = load_trial_events()
entity = st.sidebar.selectbox("Entity", ["all"] + sorted(posts["entity"].dropna().unique()))
platform = st.sidebar.selectbox("Platform", ["all"] + sorted(posts["platform"].dropna().unique()))
report_type = st.sidebar.selectbox("Report type", ["executive summary", "timeline report", "sentiment shift explanation", "topic shift explanation", "legal-event reaction report", "ThuggerDaily influence brief", "entity comparison report", "platform comparison report", "uncertainty/limitations report"])
models = list_ollama_models()
model = st.sidebar.selectbox("Ollama model", models or ["llama3.1", "mistral", "qwen2.5", "phi3"])
max_examples = st.sidebar.slider("Max example posts", 0, 10, 3)
df = posts.copy()
if entity != "all":
    df = df[df["entity"] == entity]
if platform != "all":
    df = df[df["platform"] == platform]
metrics = df.groupby(["entity", "platform"]).agg(n_records=("post_id", "count"), mean_sentiment=("sentiment_score", "mean"), total_engagement=("total_engagement", "sum")).reset_index()
examples = df.sort_values("total_engagement", ascending=False)["text"].head(max_examples).tolist()
if st.button("Generate Report", type="primary"):
    report, used_llm = generate_llm_report(report_type, metrics, events, model=model, examples=examples)
    st.success("Generated with local Ollama." if used_llm else "Ollama unavailable; generated template-based report.")
    st.markdown(report)
else:
    st.dataframe(metrics, use_container_width=True, hide_index=True)
