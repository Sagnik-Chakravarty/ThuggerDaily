# data

Dashboard data layer.

## Folders

- `raw/`: intentionally ignored by git; place private raw extracts here only for local work.
- `sample/`: small demo/sample CSVs that exercise app behavior.
- `processed/`: standardized dashboard-ready CSVs generated from the real cleaned project data.

## Rebuild Processed Data

```bash
python scripts/build_processed_data.py
```

Expected processed outputs include:

- `posts_master.csv`
- `thuggerdaily_posts.csv`
- `trial_events.csv`
- `topic_assignments.csv`
- `entity_timeseries.csv`
- `platform_summary.csv`

