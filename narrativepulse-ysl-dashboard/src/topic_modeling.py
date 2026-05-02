import pandas as pd
from .topic_leveling import calculate_topic_entropy


def aggregate_topic_prevalence(df: pd.DataFrame, group_cols=None) -> pd.DataFrame:
    group_cols = group_cols or ["platform", "entity", "topic_label"]
    counts = df.groupby(group_cols).size().reset_index(name="n_posts")
    denom_cols = [c for c in group_cols if c != "topic_label"]
    counts["topic_share"] = counts["n_posts"] / counts.groupby(denom_cols)["n_posts"].transform("sum")
    return counts


def topic_prevalence_over_time(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    counts = work.groupby([pd.Grouper(key="date", freq=freq), "entity", "platform", "topic_label"]).size().reset_index(name="n_posts")
    counts["topic_share"] = counts["n_posts"] / counts.groupby(["date", "entity", "platform"])["n_posts"].transform("sum")
    return counts


def top_words_by_topic(df: pd.DataFrame) -> pd.DataFrame:
    if "top_keywords" in df:
        return df[["topic_label", "top_keywords"]].drop_duplicates().sort_values("topic_label")
    if "topic_level_3" in df:
        return df[["topic_label", "topic_level_3"]].drop_duplicates().rename(columns={"topic_level_3": "top_keywords"})
    return pd.DataFrame(columns=["topic_label", "top_keywords"])


def representative_posts_by_topic(df: pd.DataFrame, n: int = 3) -> pd.DataFrame:
    if "text" not in df:
        return pd.DataFrame()
    return df.sort_values("engagement_rate", ascending=False, na_position="last").groupby("topic_label").head(n)


def topic_shift_pre_post(df: pd.DataFrame, event_date, window: int = 7) -> pd.DataFrame:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    event_date = pd.to_datetime(event_date)
    mask = work["date"].between(event_date - pd.Timedelta(days=window), event_date + pd.Timedelta(days=window))
    work = work[mask].copy()
    work["period"] = work["date"].lt(event_date).map({True: "pre", False: "post"})
    out = work.groupby(["period", "topic_label"]).size().reset_index(name="n_posts")
    out["topic_share"] = out["n_posts"] / out.groupby("period")["n_posts"].transform("sum")
    return out


def topic_entropy_over_time(df: pd.DataFrame, freq: str = "D") -> pd.DataFrame:
    prev = topic_prevalence_over_time(df, freq=freq)
    return prev.groupby("date")["topic_share"].apply(calculate_topic_entropy).reset_index(name="topic_entropy")
