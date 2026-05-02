import pandas as pd
from src.causal import difference_in_differences, simple_event_study


def test_simple_event_study_runs():
    df = pd.DataFrame({"date": pd.date_range("2024-01-01", periods=8), "mean_sentiment": [0, 0, 0, 0, 1, 1, 1, 1]})
    out = simple_event_study(df, "2024-01-05", "mean_sentiment", 3)
    assert out["difference"] > 0


def test_did_calculation():
    df = pd.DataFrame({
        "date": pd.to_datetime(["2024-01-01", "2024-01-06", "2024-01-01", "2024-01-06"]),
        "entity": ["A", "A", "B", "B"],
        "mean_sentiment": [1, 3, 1, 2],
    })
    out = difference_in_differences(df, "2024-01-05", "A", "B", outcome="mean_sentiment", window=7)
    assert out["did_estimate"] == 1
