import re
import pandas as pd


def standardize_dates(df: pd.DataFrame, column: str = "date") -> pd.DataFrame:
    df = df.copy()
    if column in df:
        df[column] = pd.to_datetime(df[column], errors="coerce")
    return df


def standardize_platform_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "platform" not in df:
        return df
    mapping = {
        "twitter": "X/Twitter",
        "x": "X/Twitter",
        "x/twitter": "X/Twitter",
        "youtube": "YouTube",
        "googletrends": "Google Trends",
        "news": "Newspapers",
        "newspaper": "Newspapers",
        "magazine": "Magazines",
        "local news": "Local News",
    }
    df["platform"] = df["platform"].astype(str).str.strip()
    df["platform"] = df["platform"].map(lambda x: mapping.get(x.lower(), x))
    return df


def standardize_entity_names(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    if "entity" not in df:
        return df
    mapping = {
        "young thug": "Young Thug",
        "thug": "Young Thug",
        "gunna": "Gunna",
        "yfn lucci": "YFN Lucci",
        "lucci": "YFN Lucci",
    }
    df["entity"] = df["entity"].astype(str).str.strip()
    df["entity"] = df["entity"].map(lambda x: mapping.get(x.lower(), x))
    return df


def clean_text(text):
    if pd.isna(text):
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def assign_sentiment_label(score):
    if pd.isna(score):
        return "neutral"
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


def ensure_required_columns(df: pd.DataFrame, required: list[str], defaults=None) -> pd.DataFrame:
    df = df.copy()
    defaults = defaults or {}
    for col in required:
        if col not in df:
            df[col] = defaults.get(col, pd.NA)
    return df
