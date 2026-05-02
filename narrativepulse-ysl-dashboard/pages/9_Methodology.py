import streamlit as st
from src.config import CAUSAL_CAVEAT
from src.ui_components import apply_light_theme

st.set_page_config(page_title="Methodology", layout="wide")
apply_light_theme()
st.title("Methodology")
st.info(CAUSAL_CAVEAT)
st.markdown(
    """
### Project Objective
Measure public narrative response around the YSL RICO trial timeline across platforms and entities.

### Data Collection
Sources include X/Twitter, Reddit, YouTube, Instagram, Google Trends, Spotify, Billboard, newspapers, magazines, and local news. Dashboard mode uses processed, sampled, anonymized, or demo data by default.

### Data Cleaning and Entity Identification
Records are standardized by date, platform, entity, sentiment fields, engagement fields, and topic labels. Entity comparisons focus on Young Thug, Gunna, and YFN Lucci.

### Sentiment Analysis
Sentiment scores and labels are treated as approximate public-language signals. Slang, sarcasm, legal language, and hip-hop discourse can be misclassified.

### Engagement KPI
Engagement = (Likes + Retweets + Comments) / Analytics × 100. When denominators are missing, the app uses available substitutes such as shares, views, impressions, or raw engagement counts.

### Topic Modeling and Leveling
The project used LSI/LDA-style topic modeling, Truncated SVD, t-SNE, UMASS coherence, and top-word diagnostics. Seven generalized topic groups are leveled into broad domains, clusters, and representative keywords.

### Statistical and Causal Inference
Pre/post tests, lag correlations, regressions, event studies, DiD, and interrupted time series are observational. DiD assumes parallel trends; event studies depend on timing, omitted confounders, and platform coverage.

### Local LLM Reporting
Ollama reports receive only aggregate summaries and selected examples. LLM reports summarize metrics; they are not independent evidence.

### Privacy and Data Limitations
Do not commit confidential client data, private legal records, API credentials, or raw scraped data containing sensitive user information. Public-platform samples can contain coverage bias and missingness.
"""
)
