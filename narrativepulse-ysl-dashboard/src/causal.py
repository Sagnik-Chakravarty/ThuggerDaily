import numpy as np
import pandas as pd
try:
    import statsmodels.formula.api as smf
except ModuleNotFoundError:
    smf = None
from .statistics import cohen_d, confidence_interval_mean_difference
from .config import CAUSAL_CAVEAT


def create_event_windows(df, event_date, window=7):
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    event_date = pd.to_datetime(event_date)
    work = work[work["date"].between(event_date - pd.Timedelta(days=window), event_date + pd.Timedelta(days=window))].copy()
    work["period"] = np.where(work["date"] < event_date, "pre", "post")
    work["days_from_event"] = (work["date"] - event_date).dt.days
    return work


def simple_event_study(df, event_date, outcome="mean_sentiment", window=7):
    work = create_event_windows(df, event_date, window)
    pre = work.loc[work["period"] == "pre", outcome].dropna()
    post = work.loc[work["period"] == "post", outcome].dropna()
    diff = post.mean() - pre.mean() if len(pre) and len(post) else np.nan
    ci = confidence_interval_mean_difference(pre, post)
    return {
        "pre_window": window,
        "post_window": window,
        "pre_mean": pre.mean() if len(pre) else np.nan,
        "post_mean": post.mean() if len(post) else np.nan,
        "difference": diff,
        "percent_change": diff / pre.mean() * 100 if len(pre) and pre.mean() else np.nan,
        "ci_lower": ci[0],
        "ci_upper": ci[1],
        "effect_size": cohen_d(pre, post),
        "n_pre": len(pre),
        "n_post": len(post),
        "interpretation": CAUSAL_CAVEAT,
    }


def difference_in_differences(df, event_date, treated_value, control_value, group_col="entity", outcome="mean_sentiment", window=7):
    work = create_event_windows(df[df[group_col].isin([treated_value, control_value])], event_date, window)
    work["treated"] = (work[group_col] == treated_value).astype(int)
    work["post"] = (work["period"] == "post").astype(int)
    means = work.groupby(["treated", "post"])[outcome].mean()
    did = (means.get((1, 1), np.nan) - means.get((1, 0), np.nan)) - (means.get((0, 1), np.nan) - means.get((0, 0), np.nan))
    return {"did_estimate": did, "n": len(work), "table": means.reset_index(name="mean_outcome"), "interpretation": "DiD is observational and assumes comparable pre-period trends."}


def fit_did_ols(df, event_date, treated_value, control_value, group_col="entity", outcome="mean_sentiment", window=7):
    if smf is None:
        return None
    work = create_event_windows(df[df[group_col].isin([treated_value, control_value])], event_date, window)
    work["treated"] = (work[group_col] == treated_value).astype(int)
    work["post"] = (work["period"] == "post").astype(int)
    if len(work) < 8 or work[outcome].dropna().nunique() < 2:
        return None
    return smf.ols(f"{outcome} ~ treated + post + treated:post", data=work).fit()


def interrupted_time_series(df, event_date, outcome="mean_sentiment"):
    if smf is None:
        work = df.copy()
        work["date"] = pd.to_datetime(work["date"], errors="coerce")
        return None, work
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    work = work.sort_values("date").dropna(subset=[outcome])
    event_date = pd.to_datetime(event_date)
    work["time_index"] = range(len(work))
    work["post_event"] = (work["date"] >= event_date).astype(int)
    first_post = work.loc[work["post_event"] == 1, "time_index"].min()
    work["time_after_event"] = np.where(work["post_event"] == 1, work["time_index"] - first_post + 1, 0)
    if len(work) < 10:
        return None, work
    model = smf.ols(f"{outcome} ~ time_index + post_event + time_after_event", data=work).fit()
    work["fitted"] = model.fittedvalues
    return model, work


def estimate_thuggerdaily_attribution(entity_ts, thuggerdaily_posts, event_date, entity, platform="all", outcome="mean_sentiment", window=14):
    """Estimate the share of an event-window shift temporally aligned with ThuggerDaily exposure.

    This is observational attribution, not causal responsibility. It compares the event pre/post shift
    to the post-window difference between days with ThuggerDaily exposure and days without it.
    """
    ts = entity_ts.copy()
    ts["date"] = pd.to_datetime(ts["date"], errors="coerce")
    td = thuggerdaily_posts.copy()
    td["date"] = pd.to_datetime(td["date"], errors="coerce")
    if entity != "all":
        ts = ts[ts["entity"] == entity]
        td = td[td["entity"] == entity]
    if platform != "all":
        ts = ts[ts["platform"] == platform]

    event_date = pd.to_datetime(event_date)
    windowed = create_event_windows(ts, event_date, window)
    if windowed.empty or outcome not in windowed:
        return {"status": "No event-window data available."}

    daily = windowed.groupby(["date", "period"], as_index=False)[outcome].mean()
    pre_mean = daily.loc[daily["period"] == "pre", outcome].mean()
    post_mean = daily.loc[daily["period"] == "post", outcome].mean()
    observed_shift = post_mean - pre_mean

    td_daily = td.groupby("date").agg(
        td_posts=("post_id", "count"),
        td_engagement=("total_engagement", "sum"),
        td_mean_sentiment=("sentiment_score", "mean"),
    ).reset_index()
    post_days = daily[daily["period"] == "post"].merge(td_daily, on="date", how="left")
    post_days[["td_posts", "td_engagement"]] = post_days[["td_posts", "td_engagement"]].fillna(0)
    post_days["td_exposed"] = post_days["td_posts"] > 0

    exposed = post_days.loc[post_days["td_exposed"], outcome]
    unexposed = post_days.loc[~post_days["td_exposed"], outcome]
    exposure_lift = exposed.mean() - unexposed.mean() if len(exposed) and len(unexposed) else np.nan
    share = exposure_lift / observed_shift if pd.notna(exposure_lift) and observed_shift not in [0, np.nan] else np.nan
    share = np.nan if pd.isna(share) else float(np.clip(share, -2, 2))

    return {
        "pre_mean": pre_mean,
        "post_mean": post_mean,
        "observed_shift": observed_shift,
        "td_exposed_days": int(post_days["td_exposed"].sum()),
        "post_window_days": int(len(post_days)),
        "td_posts_in_post_window": int(post_days["td_posts"].sum()),
        "td_engagement_in_post_window": float(post_days["td_engagement"].sum()),
        "exposed_day_mean": exposed.mean() if len(exposed) else np.nan,
        "unexposed_day_mean": unexposed.mean() if len(unexposed) else np.nan,
        "exposure_lift": exposure_lift,
        "attribution_share": share,
        "attribution_percent": share * 100 if pd.notna(share) else np.nan,
        "interpretation": (
            "This estimates the portion of the observed shift that is temporally aligned with ThuggerDaily exposure. "
            "It is not proof that ThuggerDaily caused that share of the change."
        ),
    }


def summarize_event_study_results(results: dict) -> str:
    return f"Post-period change was {results.get('difference', np.nan):.3f}; interpret as temporal association only."


def caveat_text() -> str:
    return CAUSAL_CAVEAT + " Results depend on timing, omitted confounders, platform coverage, and parallel-trends assumptions."
