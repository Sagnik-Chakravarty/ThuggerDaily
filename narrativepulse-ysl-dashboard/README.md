# NarrativePulse: Public Narrative Analytics Dashboard

## Overview
NarrativePulse is a professional Streamlit portfolio app for public narrative analytics around the YSL RICO trial timeline. It frames the work as legal-media intelligence: cross-platform sentiment, topic prevalence, engagement, event-linked discourse shifts, and local LLM reporting.

## Why this project matters
High-profile legal events unfold through fragmented public channels. This dashboard shows how to measure platform-level public reaction without claiming that social media definitively caused legal or public-opinion outcomes.

## Core research question
How did ThuggerDaily's X/Twitter posts temporally align with public sentiment, engagement, topic prevalence, and discourse volume around Young Thug, Gunna, and YFN Lucci across platforms?

## App features
- Executive overview with KPIs, platform/entity breakdowns, and timeline charts
- Data coverage and missingness diagnostics
- Multi-platform sentiment tracking with smoothing
- ThuggerDaily influence signal analysis with pre/post windows and lag correlations
- Topic modeling and three-level topic interpretation
- Statistical inference page with tests, effect sizes, lag analysis, and regressions
- Observational event study, DiD, and interrupted time-series page
- Optional local Ollama report generation with template fallback
- Methodology and privacy caveats

## Data sources
The project supports X/Twitter, Reddit, YouTube, Instagram, Google Trends, Spotify, Billboard, newspapers, magazines, and local news. The dashboard uses processed, sampled, anonymized, or demo data by default.

## Methods
The broader project used Python, Playwright, Selenium-based Twitter scraping, R/Quarto analysis, APIs, NLTK/TextBlob sentiment, LSI/LDA-style topic modeling, Truncated SVD, t-SNE, UMASS coherence, top-word diagnostics, event timeline mapping, and DAG thinking.

## Statistical inference
The app includes descriptive statistics, missingness checks, pre/post testing, Welch t-tests, Mann-Whitney U tests, chi-square tests, two-proportion tests, Cohen's d, confidence intervals, topic distribution shift tests, lag correlations, and regression summaries.

## Observational causal inference caveat
Event studies, DiD, and interrupted time series estimate temporal association and influence signals. They do not prove randomized causal effects. Results depend on assumptions about timing, omitted confounders, platform coverage, and parallel trends.

## Local LLM reporting with Ollama
Ollama is optional. The report generator sends only aggregate summaries and selected examples, not raw private datasets.

```bash
ollama serve
ollama pull llama3.1
ollama pull mistral
```

## Privacy and data limitations
This app is designed for portfolio demonstration using processed, public, sampled, or anonymized data. Do not commit confidential client data, private legal records, raw scraped data containing sensitive user information, or API credentials.

## Repository structure
```text
narrativepulse-ysl-dashboard/
├── app.py
├── requirements.txt
├── data/
├── src/
├── pages/
├── assets/
└── tests/
```

## Setup instructions
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Running the Streamlit app
```bash
streamlit run app.py
```

## Enabling Ollama
Start Ollama locally and pull one or more supported models. The rest of the dashboard works without Ollama.

## Screenshots placeholder
Add screenshots to `assets/app_screenshot.png` after running the app locally.

## Future work
- Replace demo data with processed CSV exports
- Add richer topic model diagnostics and embedding maps
- Add stronger event metadata and platform-specific missingness flags
- Add model cards for sentiment and topic pipelines

## Resume/portfolio positioning
This project demonstrates end-to-end analytics product work: public data collection, NLP, statistical inference, causal reasoning, dashboard engineering, and careful communication of uncertainty.
