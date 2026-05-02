import numpy as np
import pandas as pd
from src.engagement import calculate_total_engagement, calculate_engagement_rate
from src.load_data import validate_schema


def test_engagement_rate_uses_analytics():
    df = pd.DataFrame({"likes": [10], "comments": [5], "retweets": [5], "shares": [1], "analytics": [100]})
    assert calculate_total_engagement(df).iloc[0] == 20
    assert calculate_engagement_rate(df)[0] == 20


def test_missing_schema_detection():
    ok, missing = validate_schema(pd.DataFrame({"a": [1]}), ["a", "b"])
    assert not ok
    assert missing == ["b"]
