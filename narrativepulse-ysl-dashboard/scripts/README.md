# scripts

Operational scripts for building dashboard artifacts.

## `build_processed_data.py`

Reads source-specific files from `../Data/Cleaned Data/`, standardizes them into the dashboard schema, derives sentiment/topic/entity fields, computes engagement metrics, and writes processed CSVs to `data/processed/`.

Run from the dashboard folder:

```bash
python scripts/build_processed_data.py
```

## `upload_processed_to_neon.py`

Uploads the standardized processed CSVs into a Neon/Postgres database. It reads `DATABASE_URL`, `POSTGRES_URL`, `NEON_DATABASE_URL`, or `NEON_DB` from the environment, Streamlit secrets, or a local `.env` file.

```bash
python scripts/upload_processed_to_neon.py
```

The Streamlit app automatically prefers the database backend when the connection is available and falls back to local CSV/demo data otherwise.
