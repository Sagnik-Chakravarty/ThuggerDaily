import pandas as pd
from .demo_data import create_demo_trial_events


def load_default_trial_timeline() -> pd.DataFrame:
    return create_demo_trial_events()


def filter_events(events, entity="all", event_type="all"):
    out = events.copy()
    if entity != "all":
        out = out[(out["entity"] == entity) | (out["entity"] == "all")]
    if event_type != "all":
        out = out[out["event_type"] == event_type]
    return out


def align_posts_to_events(posts, events, window=7):
    rows = []
    posts = posts.copy()
    posts["date"] = pd.to_datetime(posts["date"], errors="coerce")
    for _, event in events.iterrows():
        event_date = pd.to_datetime(event["date"])
        count = posts["date"].between(event_date - pd.Timedelta(days=window), event_date + pd.Timedelta(days=window)).sum()
        rows.append({"event_id": event["event_id"], "event_name": event["event_name"], "date": event_date, "window_posts": int(count)})
    return pd.DataFrame(rows)


def create_event_overlay_data(events):
    return events.assign(date=pd.to_datetime(events["date"], errors="coerce"))
