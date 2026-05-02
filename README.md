# NarrativePulse: YSL Trial Public Narrative Analytics

NarrativePulse is a Streamlit analytics dashboard and reporting workflow for measuring public discourse around the YSL RICO trial. The project studies how public sentiment, engagement, volume, and topic prevalence shifted around key trial events, with a focused analysis of whether ThuggerDaily's X/Twitter activity was temporally aligned with downstream public narrative changes.

This is a public narrative analytics and legal-media intelligence project. It does **not** claim to determine legal truth, guilt, innocence, or definitive causal responsibility. Event-study, lag, and attribution outputs should be read as observational influence signals.

## Live App Entry Point

The deployable app lives in:

```text
narrativepulse-ysl-dashboard/app.py
```

For Streamlit Community Cloud, use this as the main file path:

```text
narrativepulse-ysl-dashboard/app.py
```

The production data backend is Neon Postgres. Add the database connection string in Streamlit secrets as either:

```toml
NEON_DB = "postgresql://..."
```

or:

```toml
DATABASE_URL = "postgresql://..."
```

Do not commit `.env`.

## Current Processed Dataset

The dashboard database currently contains:

- 165,565 unified public-discourse records
- 773 ThuggerDaily records
- May 2022 through December 2024 coverage
- Entities: Young Thug, Gunna, YFN Lucci
- Platforms: YouTube, X/Twitter, magazines, local news, newspapers, Spotify, Billboard, Instagram

The app loads data in this order:

1. Neon/Postgres when a database URL is configured and reachable
2. local processed CSVs if present
3. generated demo data as a fallback

## Local Setup

```bash
cd narrativepulse-ysl-dashboard
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

## Rebuilding Data

The cleaned source data lives under `Data/Cleaned Data/`. To rebuild dashboard-ready CSVs:

```bash
cd narrativepulse-ysl-dashboard
python scripts/build_processed_data.py
```

To upload those processed files to Neon:

```bash
python scripts/upload_processed_to_neon.py
```

## Repository Map

- `Codes/`: original collection, scraping, cleaning, and analysis notebooks/scripts
- `Data/`: raw and cleaned project source data
- `Sentiment Analysis/`: earlier sentiment-analysis outputs and Quarto artifacts
- `Topic modeling/`: topic modeling and diagnostic artifacts
- `narrativepulse-ysl-dashboard/`: deployable Streamlit app, analytics modules, tests, notebooks, report, and database scripts
- `Young Thug Time Line.rtf`: local trial timeline used alongside web-verified dates

## Report Artifacts

The LaTeX/PDF report and report figures are in:

```text
narrativepulse-ysl-dashboard/reports/
```

The report-generation notebook is:

```text
narrativepulse-ysl-dashboard/notebooks/thuggerdaily_trial_effect_report.ipynb
```

## Privacy and Security

Do not commit:

- `.env`
- API keys or database credentials
- confidential client data
- private legal records
- raw scraped data containing sensitive user information

The public app should use Neon secrets and processed/anonymized data only.
