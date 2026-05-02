import pandas as pd


def aggregate_sentiment_timeseries(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.dropna(subset=["date"])
    grouped = work.groupby([pd.Grouper(key="date", freq=freq), "platform", "entity"], dropna=False)
    out = grouped.agg(
        n_posts=("post_id", "count"),
        mean_sentiment=("sentiment_score", "mean"),
        total_engagement=("total_engagement", "sum") if "total_engagement" in work else ("likes", "sum"),
    ).reset_index()
    shares = calculate_sentiment_shares(work, freq=freq)
    return out.merge(shares, on=["date", "platform", "entity"], how="left")


def calculate_sentiment_shares(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    counts = work.groupby([pd.Grouper(key="date", freq=freq), "platform", "entity", "sentiment_label"]).size()
    wide = counts.unstack(fill_value=0).reset_index()
    total = wide[[c for c in ["positive", "negative", "neutral"] if c in wide]].sum(axis=1).replace(0, pd.NA)
    for label in ["positive", "negative", "neutral"]:
        if label not in wide:
            wide[label] = 0
        wide[f"{label}_share"] = wide[label] / total
    return wide[["date", "platform", "entity", "positive_share", "negative_share", "neutral_share"]]


def smooth_sentiment(df: pd.DataFrame, window: int = 7, group_cols=None) -> pd.DataFrame:
    work = df.sort_values("date").copy()
    group_cols = group_cols or ["platform", "entity"]
    work["smoothed_sentiment"] = work.groupby(group_cols)["mean_sentiment"].transform(lambda s: s.rolling(window, min_periods=1).mean())
    return work


def compare_sentiment_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("platform").agg(n=("post_id", "count"), mean_sentiment=("sentiment_score", "mean")).reset_index()


def compare_sentiment_by_entity(df: pd.DataFrame) -> pd.DataFrame:
    return df.groupby("entity").agg(n=("post_id", "count"), mean_sentiment=("sentiment_score", "mean")).reset_index()
