import pandas as pd
from src.statistics import pre_post_summary, cohen_d


def test_pre_post_summary_returns_difference():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=10), "sentiment_score": [0, 0, 0, 0, 0, 1, 1, 1, 1, 1]})
    out = pre_post_summary(df, "2024-01-06", "sentiment_score", 3)
    assert out["pre_n"] == 3
    assert out["post_n"] == 4
    assert out["difference"] > 0


def test_cohen_d_zero_variance_safe():
    assert pd.isna(cohen_d([1, 1], [1, 1]))
