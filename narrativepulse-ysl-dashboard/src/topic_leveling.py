import numpy as np
import pandas as pd
from .config import TOPIC_LEVEL_MAP


def map_topic_to_broad_domain(topic_label: str) -> str:
    return TOPIC_LEVEL_MAP.get(str(topic_label), ("media/news", "general media discourse", ""))[0]


def assign_topic_levels(df: pd.DataFrame) -> pd.DataFrame:
    work = df.copy()
    if "topic_label" not in work:
        work["topic_label"] = "Trial-related Content"
    levels = work["topic_label"].map(lambda x: TOPIC_LEVEL_MAP.get(str(x), ("media/news", "general media discourse", "news, coverage, public")))
    work["topic_level_1"] = levels.map(lambda x: x[0])
    work["topic_level_2"] = levels.map(lambda x: x[1])
    work["topic_level_3"] = levels.map(lambda x: x[2])
    return work


def calculate_topic_entropy(shares) -> float:
    vals = pd.Series(shares, dtype=float).dropna()
    vals = vals[vals > 0]
    if vals.empty:
        return 0.0
    return float(-(vals * np.log(vals)).sum())


def calculate_hhi(shares) -> float:
    vals = pd.Series(shares, dtype=float).dropna()
    return float((vals ** 2).sum())


def topic_level_summary(df: pd.DataFrame) -> pd.DataFrame:
    work = assign_topic_levels(df)
    return work.groupby(["topic_level_1", "topic_level_2", "topic_label"]).size().reset_index(name="n_records")
