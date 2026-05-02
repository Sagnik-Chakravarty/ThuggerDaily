import numpy as np
import pandas as pd
from scipy import stats
try:
    import statsmodels.api as sm
    import statsmodels.formula.api as smf
except ModuleNotFoundError:  # Allows non-regression utilities to run before full dependency install.
    sm = None
    smf = None


def descriptive_summary(df: pd.DataFrame) -> pd.DataFrame:
    cols = [c for c in ["sentiment_score", "engagement_rate", "total_engagement", "likes", "comments", "shares"] if c in df]
    if not cols:
        return pd.DataFrame()
    return df[cols].describe().T.assign(iqr=lambda x: x["75%"] - x["25%"]).reset_index(names="metric")


def missingness_summary(df: pd.DataFrame, by=None) -> pd.DataFrame:
    if by and by in df:
        return df.groupby(by).apply(lambda g: g.isna().mean(), include_groups=False).reset_index()
    return df.isna().mean().reset_index(name="missing_rate").rename(columns={"index": "field"})


def duplicate_summary(df: pd.DataFrame) -> dict:
    subset = ["post_id"] if "post_id" in df else None
    return {"n_rows": len(df), "n_duplicate_rows": int(df.duplicated(subset=subset).sum())}


def _window_values(df, event_date, outcome, window):
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    event_date = pd.to_datetime(event_date)
    pre = work[work["date"].between(event_date - pd.Timedelta(days=window), event_date - pd.Timedelta(days=1))][outcome].dropna()
    post = work[work["date"].between(event_date, event_date + pd.Timedelta(days=window))][outcome].dropna()
    return pre, post


def cohen_d(a, b) -> float:
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 2 or len(b) < 2:
        return np.nan
    pooled = np.sqrt(((len(a) - 1) * a.var(ddof=1) + (len(b) - 1) * b.var(ddof=1)) / (len(a) + len(b) - 2))
    return np.nan if pooled == 0 else float((b.mean() - a.mean()) / pooled)


def confidence_interval_mean_difference(a, b, alpha=0.05):
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 2 or len(b) < 2:
        return (np.nan, np.nan)
    diff = b.mean() - a.mean()
    se = np.sqrt(a.var(ddof=1) / len(a) + b.var(ddof=1) / len(b))
    z = stats.norm.ppf(1 - alpha / 2)
    return float(diff - z * se), float(diff + z * se)


def welch_t_test(a, b) -> dict:
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 2 or len(b) < 2:
        return {"statistic": np.nan, "p_value": np.nan}
    stat, p = stats.ttest_ind(a, b, equal_var=False, nan_policy="omit")
    return {"statistic": float(stat), "p_value": float(p)}


def mann_whitney_test(a, b) -> dict:
    a, b = pd.Series(a).dropna(), pd.Series(b).dropna()
    if len(a) < 1 or len(b) < 1:
        return {"statistic": np.nan, "p_value": np.nan}
    stat, p = stats.mannwhitneyu(a, b, alternative="two-sided")
    return {"statistic": float(stat), "p_value": float(p)}


def chi_square_test(table) -> dict:
    chi2, p, dof, expected = stats.chi2_contingency(table)
    return {"chi2": float(chi2), "p_value": float(p), "dof": int(dof)}


def two_proportion_test(success_a, n_a, success_b, n_b) -> dict:
    if min(n_a, n_b) == 0:
        return {"z": np.nan, "p_value": np.nan, "difference": np.nan}
    p1, p2 = success_a / n_a, success_b / n_b
    pooled = (success_a + success_b) / (n_a + n_b)
    se = np.sqrt(pooled * (1 - pooled) * (1 / n_a + 1 / n_b))
    z = np.nan if se == 0 else (p2 - p1) / se
    p = np.nan if pd.isna(z) else 2 * (1 - stats.norm.cdf(abs(z)))
    return {"z": float(z), "p_value": float(p), "difference": float(p2 - p1)}


def pre_post_summary(df, event_date, outcome="sentiment_score", window=7) -> dict:
    pre, post = _window_values(df, event_date, outcome, window)
    diff = post.mean() - pre.mean() if len(pre) and len(post) else np.nan
    ci_low, ci_high = confidence_interval_mean_difference(pre, post)
    t = welch_t_test(pre, post)
    return {
        "outcome": outcome,
        "pre_n": int(len(pre)),
        "post_n": int(len(post)),
        "pre_mean": float(pre.mean()) if len(pre) else np.nan,
        "post_mean": float(post.mean()) if len(post) else np.nan,
        "difference": float(diff) if pd.notna(diff) else np.nan,
        "percent_change": float(diff / pre.mean() * 100) if len(pre) and pre.mean() not in [0, np.nan] else np.nan,
        "ci_lower": ci_low,
        "ci_upper": ci_high,
        "p_value": t["p_value"],
        "effect_size": cohen_d(pre, post),
        "interpretation": "Exploratory pre/post association; timing alone is not causal evidence.",
    }


def topic_distribution_shift_test(df, event_date, window=7) -> dict:
    work = df.copy()
    work["date"] = pd.to_datetime(work["date"], errors="coerce")
    event_date = pd.to_datetime(event_date)
    work = work[work["date"].between(event_date - pd.Timedelta(days=window), event_date + pd.Timedelta(days=window))]
    work["period"] = np.where(work["date"] < event_date, "pre", "post")
    table = pd.crosstab(work["period"], work["topic_label"])
    if table.shape[0] < 2 or table.shape[1] < 2:
        return {"p_value": np.nan, "table": table}
    return {**chi_square_test(table), "table": table}


def lag_correlation(exposure_df, outcome_df, exposure_col="n_posts", outcome_col="n_posts", lags=(0, 1, 3, 7, 14)) -> pd.DataFrame:
    e = exposure_df.copy()
    o = outcome_df.copy()
    e["date"] = pd.to_datetime(e["date"])
    o["date"] = pd.to_datetime(o["date"])
    daily_e = e.groupby("date")[exposure_col].sum().rename("exposure")
    daily_o = o.groupby("date")[outcome_col].sum().rename("outcome")
    base = pd.concat([daily_e, daily_o], axis=1).fillna(0)
    rows = []
    for lag in lags:
        corr = base["exposure"].corr(base["outcome"].shift(-lag))
        rows.append({"lag_days": lag, "correlation": corr})
    return pd.DataFrame(rows)


def regression_sentiment_ols(df):
    if smf is None:
        return None
    work = df.dropna(subset=["sentiment_score"]).copy()
    if len(work) < 10:
        return None
    return smf.ols("sentiment_score ~ C(platform) + C(entity) + C(topic_label)", data=work).fit()


def regression_positive_logit(df):
    if smf is None:
        return None
    work = df.dropna(subset=["sentiment_label"]).copy()
    work["positive"] = (work["sentiment_label"] == "positive").astype(int)
    if work["positive"].nunique() < 2 or len(work) < 20:
        return None
    return smf.logit("positive ~ C(platform) + C(entity)", data=work).fit(disp=False)


def regression_volume_poisson(entity_ts):
    if smf is None or sm is None:
        return None
    work = entity_ts.dropna(subset=["n_posts"]).copy()
    if len(work) < 10:
        return None
    return smf.glm("n_posts ~ C(platform) + C(entity)", data=work, family=sm.families.Poisson()).fit()
