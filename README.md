# ThuggerDaily / NarrativePulse

ThuggerDaily / NarrativePulse is a public narrative analytics project focused on discourse around the YSL RICO trial, Young Thug, Gunna, YFN Lucci, and ThuggerDaily activity. The repository combines original data collection and cleaning notebooks, topic-modeling work, statistical analysis, and a deployable Streamlit dashboard.

The project is framed as legal-media and public discourse measurement. It estimates temporal alignment, sentiment shifts, engagement patterns, topic prevalence, and event-linked narrative signals. It does not claim to prove legal causality, court impact, or definitive public opinion change.

## Main Dashboard

The Streamlit app lives in [`narrativepulse-ysl-dashboard/`](narrativepulse-ysl-dashboard/).

Core dashboard features include:

- Executive KPIs and cross-platform summary
- Data source and coverage diagnostics
- Multi-platform sentiment trends
- ThuggerDaily influence-signal analysis
- Topic modeling and topic-level interpretation
- Statistical inference, including pre/post tests, effect sizes, lag correlations, and regression summaries
- Causal-style event study views with attribution caveats
- Timeline report generation with local Ollama support and a template fallback
- Methodology and privacy documentation

## Repository Structure

```text
.
|-- Codes/
|   |-- Data Collection/
|   `-- Data Cleaning/
|-- Topic modeling/
|-- narrativepulse-ysl-dashboard/
|   |-- app.py
|   |-- pages/
|   |-- src/
|   |-- scripts/
|   |-- data/
|   |-- notebooks/
|   |-- reports/
|   `-- tests/
|-- requirements.txt
`-- README.md
```

## Quick Start

From the repository root:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cd narrativepulse-ysl-dashboard
streamlit run app.py
```

The dashboard loads data in this order:

1. Neon/Postgres, if `DATABASE_URL` or `NEON_DB` is configured.
2. Local processed CSV files in `narrativepulse-ysl-dashboard/data/processed/`.
3. Generated demo data as a fallback.

## Data Pipeline

Original collection and cleaning work is stored in [`Codes/`](Codes/). Topic modeling experiments and visual diagnostics are stored in [`Topic modeling/`](Topic%20modeling/).

The dashboard expects standardized processed outputs such as:

- `posts_master.csv`
- `thuggerdaily_posts.csv`
- `trial_events.csv`
- `topic_assignments.csv`
- `entity_timeseries.csv`
- `platform_summary.csv`

To rebuild processed dashboard data:

```bash
cd narrativepulse-ysl-dashboard
python scripts/build_processed_data.py
```

To upload processed data to Neon/Postgres:

```bash
cd narrativepulse-ysl-dashboard
python scripts/upload_processed_to_neon.py
```

Large raw and processed data files should not be committed.

## Deployment

For Streamlit Community Cloud, use:

```text
Main file path: narrativepulse-ysl-dashboard/app.py
```

Configure one of the following secrets:

```toml
DATABASE_URL = "postgresql://..."
```

or:

```toml
NEON_DB = "postgresql://..."
```

Detailed deployment notes are in [`narrativepulse-ysl-dashboard/DEPLOYMENT.md`](narrativepulse-ysl-dashboard/DEPLOYMENT.md).

## Tests

Dashboard tests are under [`narrativepulse-ysl-dashboard/tests/`](narrativepulse-ysl-dashboard/tests/). Run them from the dashboard directory:

```bash
cd narrativepulse-ysl-dashboard
pytest
```

## Methods

The project uses Python data engineering, cross-platform schema standardization, sentiment scoring, engagement normalization, topic modeling, event-window analysis, exploratory lag correlations, and observational causal-inference-style summaries.

All findings should be interpreted as descriptive or temporal-association evidence unless supported by a specific statistical design and clearly stated assumptions.

## Privacy And Data Handling

This repository is intended for portfolio and research demonstration using public or processed data. Do not commit credentials, private legal records, confidential source material, raw scraped data containing sensitive fields, or local `.env` files.
