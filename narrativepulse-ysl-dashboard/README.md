# NarrativePulse Dashboard

NarrativePulse is a deployable Streamlit dashboard for public narrative analytics around the YSL RICO trial. It measures cross-platform sentiment, engagement, discourse volume, topic prevalence, event-window shifts, and ThuggerDaily-aligned influence signals.

The dashboard is designed as a professional legal-media intelligence product, not a celebrity gossip app. It uses careful observational language and avoids unsupported causal or legal claims.

## Main Research Question

How did ThuggerDaily's X/Twitter posts temporally align with public sentiment, engagement, topic prevalence, and discourse volume around Young Thug, Gunna, and YFN Lucci across platforms?

## Core Features

- Executive KPIs and cross-platform summary
- Data source and coverage diagnostics
- Multi-platform sentiment trends
- ThuggerDaily influence-signal analysis
- Topic modeling and topic-level interpretation
- Statistical inference: pre/post tests, effect sizes, lag correlations, regression summaries
- Causal-style event study: event windows, DiD, interrupted time series, attribution caveats
- Local Ollama report generator with template fallback
- Methodology and privacy documentation

## Data Backend

The app supports three data modes:

1. **Neon/Postgres**: production deployment path
2. **Local processed CSVs**: development mode
3. **Generated demo data**: fallback mode

For deployment, configure Streamlit secrets with:

```toml
NEON_DB = "postgresql://..."
```

or:

```toml
DATABASE_URL = "postgresql://..."
```

The app will show `Data backend: Neon Postgres` in the sidebar when connected.

## Current Database Tables

The production database expects:

- `posts_master`
- `thuggerdaily_posts`
- `trial_events`
- `topic_assignments`
- `entity_timeseries`
- `platform_summary`

Upload/refresh them with:

```bash
python scripts/upload_processed_to_neon.py
```

## Local Development

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Streamlit Cloud Deployment

Use:

```text
Main file path: narrativepulse-ysl-dashboard/app.py
```

Add the Neon URL in Streamlit secrets. Do not commit `.env`.

More detailed instructions are in [DEPLOYMENT.md](DEPLOYMENT.md).

## Rebuilding Processed Data

The adapter reads source-specific cleaned files from `../Data/Cleaned Data/` and writes standardized CSVs to `data/processed/`:

```bash
python scripts/build_processed_data.py
```

Large processed CSVs are intentionally ignored by git because the deployed app reads from Neon.

## Project Structure

```text
narrativepulse-ysl-dashboard/
├── app.py
├── pages/
├── src/
├── scripts/
├── data/
├── notebooks/
├── reports/
├── tests/
├── assets/
├── requirements.txt
└── DEPLOYMENT.md
```

## Methods

The project uses:

- Python data engineering and schema standardization
- TextBlob-style sentiment scoring
- engagement normalization using likes, retweets/shares, comments, views, and analytics fields
- seven generalized topic groups with three-level topic interpretation
- event-window analysis around trial dates
- exploratory lag correlations
- observational causal-inference-style summaries
- local LLM report generation through Ollama when available

## Causal Caveat

This app estimates temporal association, event-linked discourse shifts, and public narrative influence signals. It does not prove that ThuggerDaily caused legal outcomes, changed court decisions, or definitively caused public opinion changes.

## Privacy

This app is built for portfolio demonstration using processed public data. Do not commit credentials, private legal records, confidential client data, or sensitive raw scraped data.
