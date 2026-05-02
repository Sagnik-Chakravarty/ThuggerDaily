# Data

Source data for the project.

## Contents

- `UnCleaned Data/`: raw or minimally transformed source exports. Treat this as sensitive working data and avoid exposing it in a public portfolio.
- `Cleaned Data/`: cleaned source-specific exports used by the dashboard ingestion script.

The Streamlit dashboard does not read these source files directly at runtime. Instead, run:

```bash
cd narrativepulse-ysl-dashboard
python scripts/build_processed_data.py
```

That script writes standardized dashboard-ready CSVs into `narrativepulse-ysl-dashboard/data/processed/`.

