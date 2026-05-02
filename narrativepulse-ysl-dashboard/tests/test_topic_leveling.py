import numpy as np
import pandas as pd
from src.topic_leveling import assign_topic_levels, calculate_topic_entropy, calculate_hhi


def test_topic_levels_assigned():
    df = assign_topic_levels(pd.DataFrame({"topic_label": ["Free Thug Support"]}))
    assert df.loc[0, "topic_level_1"] == "fandom/support"


def test_entropy_and_hhi():
    shares = [0.5, 0.5]
    assert np.isclose(calculate_topic_entropy(shares), 0.6931471805599453)
    assert calculate_hhi(shares) == 0.5
