# NarrativePulse: YSL Trial Public Narrative Analytics

NarrativePulse is a Streamlit analytics dashboard and reporting workflow for measuring public discourse around the YSL RICO trial. The project studies how public sentiment, engagement, volume, and topic prevalence shifted around key trial events, with a focused analysis of whether ThuggerDaily's X/Twitter activity was temporally aligned with downstream public narrative changes.

This is a public narrative analytics and legal-media intelligence project. It does **not** claim to determine legal truth, guilt, innocence, or definitive causal responsibility. Event-study, lag, and attribution outputs should be read as observational influence signals.

## Quick Links

- Live dashboard: https://narrativepulse.streamlit.app/
- GitHub repository: https://github.com/Sagnik-Chakravarty/ThuggerDaily
- Report PDF (local path): `narrativepulse-ysl-dashboard/reports/narrativepulse_thuggerdaily_trial_report.pdf`

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

## Results (At a Glance)

These results are phrased conservatively and should be read as *observational narrative signals*, not definitive causal attribution.

**KPIs**

| KPI | Value |
|---|---:|
| Unified public-discourse records | 165,565 |
| Platforms covered | 8 |
| Entities tracked | 3 |
| Topic groups (leveled) | 7 |
| Coverage window (public corpus) | 2022-05-01 to 2024-12-29 |
| ThuggerDaily posts (exposure stream) | 773 |
| ThuggerDaily coverage window | 2023-01-01 to 2024-12-07 |
| Key trial events table (dashboard default) | 7 |

**Headline findings**

- Public discourse shifts are most pronounced around major legal moments (attention/volume and engagement move more consistently than sentiment).
- ThuggerDaily activity is frequently present in the same short post-event windows where cross-platform attention is moving; the most defensible interpretation is *amplification/framing during already-salient events*.
- Full-period lag correlations are small, suggesting any influence is episodic and event-conditioned rather than a stable long-run predictor.
- Topic shifts provide a clearer interpretation layer than sentiment alone (e.g., resolution moments tend to rebalance discourse toward music/fandom framing vs procedural/legal language).

## Local Setup

```bash
cd narrativepulse-ysl-dashboard
python3 -m venv .venv
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
