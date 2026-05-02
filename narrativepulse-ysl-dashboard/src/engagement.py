import numpy as np
import pandas as pd


def calculate_total_engagement(df: pd.DataFrame) -> pd.Series:
    likes = pd.to_numeric(df.get("likes", 0), errors="coerce").fillna(0)
    comments = pd.to_numeric(df.get("comments", 0), errors="coerce").fillna(0)
    shares = pd.to_numeric(df.get("shares", 0), errors="coerce").fillna(0)
    retweets = pd.to_numeric(df.get("retweets", shares), errors="coerce").fillna(0)
    return likes + comments + np.maximum(shares, retweets)


def calculate_engagement_rate(df: pd.DataFrame) -> pd.Series:
    total = calculate_total_engagement(df)
    denominator = pd.to_numeric(df.get("analytics", pd.Series(index=df.index, dtype=float)), errors="coerce")
    if denominator.isna().all():
        denominator = pd.to_numeric(df.get("views", pd.Series(index=df.index, dtype=float)), errors="coerce")
    return np.where(denominator.fillna(0) > 0, total / denominator * 100, np.nan)


def aggregate_engagement_by_platform(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["total_engagement"] = calculate_total_engagement(work)
    return work.groupby("platform", dropna=False).agg(
        n_records=("post_id", "count"),
        total_engagement=("total_engagement", "sum"),
        mean_engagement=("total_engagement", "mean"),
        mean_engagement_rate=("engagement_rate", "mean"),
    ).reset_index()


def aggregate_engagement_by_entity(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    work["total_engagement"] = calculate_total_engagement(work)
    return work.groupby("entity", dropna=False).agg(
        n_records=("post_id", "count"),
        total_engagement=("total_engagement", "sum"),
        mean_engagement=("total_engagement", "mean"),
    ).reset_index()


def identify_engagement_spikes(df: pd.DataFrame, z_threshold: float = 2.0) -> pd.DataFrame:
    work = df.copy()
    if "total_engagement" not in work:
        work["total_engagement"] = calculate_total_engagement(work)
    std = work["total_engagement"].std(ddof=0)
    work["engagement_z"] = 0 if not std else (work["total_engagement"] - work["total_engagement"].mean()) / std
    return work[work["engagement_z"] >= z_threshold].sort_values("engagement_z", ascending=False)
