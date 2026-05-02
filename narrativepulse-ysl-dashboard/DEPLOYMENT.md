# Streamlit Cloud Deployment

This app is deployable with Neon Postgres as the production data backend.

## 1. Push the repo to GitHub

Do **not** commit `.env` or the large local generated CSVs in `data/processed/`. The app reads production data from Neon when `DATABASE_URL` or `NEON_DB` is configured.

## 2. Streamlit Cloud settings

In Streamlit Community Cloud:

- Repository: this repo
- Branch: your deployment branch
- Main file path: `narrativepulse-ysl-dashboard/app.py`

## 3. Add secrets

In Streamlit Cloud app settings, add one of these secrets:

```toml
DATABASE_URL = "postgresql://..."
```

or:

```toml
NEON_DB = "postgresql://..."
```

The local `.env` file can use the same key, but it must not be committed.

## 4. Database tables

The app expects these Neon/Postgres tables:

- `posts_master`
- `thuggerdaily_posts`
- `trial_events`
- `topic_assignments`
- `entity_timeseries`
- `platform_summary`

Upload or refresh them locally with:

```bash
cd narrativepulse-ysl-dashboard
source .venv/bin/activate
python scripts/upload_processed_to_neon.py
```

## 5. Runtime behavior

The app load order is:

1. Neon/Postgres if a database URL is configured and reachable.
2. Local processed CSVs if present.
3. Generated demo data as a fallback.

Production deployment should use option 1.

