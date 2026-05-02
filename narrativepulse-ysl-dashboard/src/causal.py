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


def summarize_event_study_results(results: dict) -> str:
    return f"Post-period change was {results.get('difference', np.nan):.3f}; interpret as temporal association only."


def caveat_text() -> str:
    return CAUSAL_CAVEAT + " Results depend on timing, omitted confounders, platform coverage, and parallel-trends assumptions."
