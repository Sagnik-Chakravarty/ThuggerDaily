from __future__ import annotations

import re
from pathlib import Path
import numpy as np
import pandas as pd
from textblob import TextBlob

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
SOURCE_ROOT = REPO / "Data" / "Cleaned Data"
OUT = ROOT / "data" / "processed"

ENTITIES = ["Young Thug", "Gunna", "YFN Lucci"]
TOPIC_KEYWORDS = {
    "Live Music in Atlanta": ["atlanta", "venue", "concert", "stage", "festival", "hawks", "state farm"],
    "Slang": ["slatt", "slime", "twin", "cap", "snitch", "rat", "street"],
    "Trial-related Content": ["trial", "rico", "ysl", "indictment", "testimony", "witness", "jury", "verdict"],
    "Legal System and Judicial Process": ["judge", "court", "plea", "bond", "motion", "attorney", "prosecutor", "jail", "sentence"],
    "Music": ["song", "album", "track", "music", "spotify", "billboard", "chart", "release"],
    "Social Media Slang and Emojis": ["emoji", "instagram", "twitter", "tweet", "viral", "meme", "comment"],
    "Free Thug Support": ["free thug", "freethug", "support", "protect black art", "release", "home"],
}
TOPIC_LEVEL_MAP = {
    "Live Music in Atlanta": ("local Atlanta culture", "local venue/music scene", "atlanta, venue, show, stage"),
    "Slang": ("slang/social media", "social media slang", "slang, phrase, reaction"),
    "Trial-related Content": ("legal", "trial/legal process", "trial, court, testimony"),
    "Legal System and Judicial Process": ("legal", "trial/legal process", "judge, motion, plea"),
    "Music": ("music", "music releases", "album, song, chart"),
    "Social Media Slang and Emojis": ("slang/social media", "social media slang", "emoji, meme, viral"),
    "Free Thug Support": ("fandom/support", "Free Thug support", "support, free, fan"),
}


def clean_text(value) -> str:
    if pd.isna(value):
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def first_present(df, candidates):
    lower = {c.lower(): c for c in df.columns}
    for c in candidates:
        if c.lower() in lower:
            return lower[c.lower()]
    return None


def parse_date(series):
    dates = pd.to_datetime(series, errors="coerce", utc=True).dt.tz_convert(None)
    return dates


def sentiment_score(text: str) -> float:
    if not text:
        return 0.0
    try:
        return float(TextBlob(text[:5000]).sentiment.polarity)
    except Exception:
        return 0.0


def sentiment_label(score: float) -> str:
    if score > 0.1:
        return "positive"
    if score < -0.1:
        return "negative"
    return "neutral"


def infer_entity(row_text: str, keywords: str = "", fallback: str = "") -> str | None:
    text = f"{row_text} {keywords} {fallback}".lower()
    scores = {
        "Young Thug": any(x in text for x in ["young thug", "thugger", "jeffrey williams", "jeffrey lamar", "ysl", "young slime life"]),
        "Gunna": any(x in text for x in ["gunna", "sergio kitchens", "sergio"]),
        "YFN Lucci": any(x in text for x in ["yfn lucci", "lucci", "rayshawn bennett", "rayshawn"]),
    }
    hits = [k for k, v in scores.items() if v]
    if hits:
        return hits[0]
    return None


def infer_topic(text: str) -> str:
    lower = text.lower()
    best = ("Trial-related Content", 0)
    for topic, words in TOPIC_KEYWORDS.items():
        score = sum(1 for w in words if w in lower)
        if score > best[1]:
            best = (topic, score)
    return best[0]


def platform_from_path(path: Path) -> tuple[str, str]:
    rel = str(path).lower()
    name = path.stem.lower()
    if "billboard" in rel:
        return "Billboard", "music"
    if "newspaper" in rel:
        return "Newspapers", "newspapers"
    if "magazine" in rel:
        return "Magazines", "magazines"
    if "news station" in rel:
        return ("YouTube" if "youtube" in name else "Local News"), "local news"
    if "reddit" in name:
        return "Reddit", "social media"
    if "instagram" in name:
        return "Instagram", "social media"
    if "youtube" in name or "lawandorder" in name:
        return "YouTube", "video"
    if "spotify" in name or "kingslime" in name:
        return "Spotify", "music"
    if "googletrends" in name:
        return "Google Trends", "search"
    if "twitter" in name or name == "ysl" or "thuggerdaily" in name:
        return "X/Twitter", "social media"
    return path.parent.name, "other"


def read_source(path: Path) -> pd.DataFrame:
    if path.suffix.lower() == ".xlsx":
        return pd.read_excel(path)
    return pd.read_csv(path)


def normalize_file(path: Path) -> pd.DataFrame:
    df = read_source(path)
    if df.empty:
        return pd.DataFrame()
    platform, source_group = platform_from_path(path)

    date_col = first_present(df, ["Timestamp", "Published Date", "publication_date", "timestamp", "published_at", "published at", "upload_date", "release_date", "Release Date", "date", "chart_week", "creation_year"])
    if date_col is None:
        return pd.DataFrame()
    dates = parse_date(df[date_col])

    text_cols = [c for c in [
        first_present(df, ["Tweets", "caption", "comment", "title", "headlines", "headline", "name", "Name"]),
        first_present(df, ["snippet", "snippets", "description"]),
        first_present(df, ["article", "text"]),
    ] if c]
    if not text_cols:
        text_cols = [c for c in df.columns if c.lower() in ["performer", "artist", "channel_title"]]
    text = df[text_cols].fillna("").astype(str).agg(" ".join, axis=1).map(clean_text)

    keywords_col = first_present(df, ["Keywords", "Search Term", "search term", "Artist", "performer", "channel_title"])
    keywords = df[keywords_col].fillna("").astype(str) if keywords_col else pd.Series([""] * len(df), index=df.index)
    entity = [infer_entity(t, k) for t, k in zip(text, keywords)]

    likes_col = first_present(df, ["Likes", "likes", "like_count", "video likes", "comment likes", "Popularity", "current_week"])
    comments_col = first_present(df, ["Comments", "comments", "comments_count", "total comment", "replies"])
    retweets_col = first_present(df, ["Retweets"])
    views_col = first_present(df, ["views", "view_count", "Analytics", "subscribers"])
    analytics_col = first_present(df, ["Analytics", "views", "view_count"])
    url_col = first_present(df, ["links", "link", "url"])
    author_col = first_present(df, ["Name", "Handle", "subreddit", "Source", "channel_title", "Artist", "performer"])

    out = pd.DataFrame({
        "post_id": [f"{path.stem}_{i}" for i in range(len(df))],
        "platform": platform,
        "source_group": source_group,
        "date": dates,
        "text": text,
        "author": df[author_col].astype(str) if author_col else path.stem,
        "entity": entity,
        "likes": pd.to_numeric(df[likes_col], errors="coerce") if likes_col else np.nan,
        "comments": pd.to_numeric(df[comments_col], errors="coerce") if comments_col else np.nan,
        "shares": np.nan,
        "retweets": pd.to_numeric(df[retweets_col], errors="coerce") if retweets_col else np.nan,
        "views": pd.to_numeric(df[views_col], errors="coerce") if views_col else np.nan,
        "analytics": pd.to_numeric(df[analytics_col], errors="coerce") if analytics_col else np.nan,
        "url": df[url_col].astype(str) if url_col else "",
        "source_file": str(path.relative_to(REPO)),
    })
    out = out.dropna(subset=["date"])
    out = out[out["date"].between(pd.Timestamp("2022-05-01"), pd.Timestamp("2024-12-31"))]
    out = out[out["entity"].notna()]
    out = out[out["text"].str.len() > 0]
    if out.empty:
        return out

    out["sentiment_score"] = out["text"].map(sentiment_score)
    out["sentiment_label"] = out["sentiment_score"].map(sentiment_label)
    out["topic_label"] = out["text"].map(infer_topic)
    out["topic_id"] = out["topic_label"].map(lambda t: list(TOPIC_KEYWORDS).index(t) + 1)
    levels = out["topic_label"].map(TOPIC_LEVEL_MAP)
    out["topic_level_1"] = levels.map(lambda x: x[0])
    out["topic_level_2"] = levels.map(lambda x: x[1])
    out["topic_level_3"] = levels.map(lambda x: x[2])
    total = out[["likes", "comments", "shares", "retweets"]].fillna(0)
    out["total_engagement"] = total["likes"] + total["comments"] + np.maximum(total["shares"], total["retweets"])
    denom = out["analytics"].fillna(out["views"])
    out["engagement_rate"] = np.where(denom.fillna(0) > 0, out["total_engagement"] / denom * 100, np.nan)
    if "thuggerdaily" in path.stem.lower():
        out["author"] = "ThuggerDaily"
    return out


def trial_events() -> pd.DataFrame:
    rows = [
        ("evt_2022_05_indictment", "2022-05-09", "YSL indictment announced", "legal", "Young Thug", "Public indictment and arrests begin the main timeline.", "Project timeline"),
        ("evt_2022_12_gunna_plea", "2022-12-14", "Gunna enters Alford plea and is released", "legal", "Gunna", "Gunna plea becomes a major public narrative event.", "Project timeline"),
        ("evt_2023_01_jury", "2023-01-04", "Jury selection begins", "legal", "Young Thug", "Extended jury selection period begins.", "Project timeline"),
        ("evt_2023_11_opening", "2023-11-27", "Opening statements begin", "legal", "Young Thug", "Trial proceedings move into opening statements.", "Project timeline"),
        ("evt_2024_07_recusal", "2024-07-15", "Judge recusal period", "legal", "Young Thug", "Judge recusal creates a high-visibility procedural shift.", "Project timeline"),
        ("evt_2024_10_plea", "2024-10-31", "Young Thug plea and release", "legal", "Young Thug", "Young Thug reaches plea agreement and is released.", "Project timeline"),
        ("evt_2024_12_media", "2024-12-03", "Post-resolution media cycle", "media", "all", "Follow-on media and social discourse after case resolution.", "Project timeline"),
    ]
    return pd.DataFrame(rows, columns=["event_id", "date", "event_name", "event_type", "entity", "description", "source"])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    files = list((SOURCE_ROOT / "Sentiment Analysis").glob("**/*.csv")) + list((SOURCE_ROOT / "Sentiment Analysis").glob("**/*.xlsx")) + list((SOURCE_ROOT / "Billboard").glob("*.csv"))
    frames = []
    errors = []
    for path in sorted(files):
        try:
            norm = normalize_file(path)
            if not norm.empty:
                frames.append(norm)
        except Exception as exc:
            errors.append({"file": str(path.relative_to(REPO)), "error": str(exc)})
    if not frames:
        raise SystemExit("No usable source rows found.")
    posts = pd.concat(frames, ignore_index=True)
    posts = posts.sort_values("date").reset_index(drop=True)
    posts["post_id"] = [f"real_{i:08d}" for i in range(len(posts))]
    ordered = [
        "post_id", "platform", "date", "text", "author", "entity", "sentiment_score", "sentiment_label",
        "likes", "comments", "shares", "retweets", "views", "analytics", "engagement_rate", "topic_id",
        "topic_label", "topic_level_1", "topic_level_2", "topic_level_3", "url", "total_engagement",
        "source_group", "source_file",
    ]
    posts[ordered].to_csv(OUT / "posts_master.csv", index=False)
    thugger = posts[posts["author"].astype(str).str.lower().eq("thuggerdaily")].copy()
    thugger.to_csv(OUT / "thuggerdaily_posts.csv", index=False)

    topics = posts[["post_id", "date", "platform", "entity", "topic_id", "topic_label", "topic_level_1", "topic_level_2", "topic_level_3"]].copy()
    topics["top_keywords"] = topics["topic_level_3"]
    topics.to_csv(OUT / "topic_assignments.csv", index=False)

    entity_ts = posts.groupby([posts["date"].dt.date, "platform", "entity"]).agg(
        n_posts=("post_id", "count"),
        mean_sentiment=("sentiment_score", "mean"),
        positive_share=("sentiment_label", lambda s: (s == "positive").mean()),
        negative_share=("sentiment_label", lambda s: (s == "negative").mean()),
        neutral_share=("sentiment_label", lambda s: (s == "neutral").mean()),
        total_engagement=("total_engagement", "sum"),
        mean_engagement=("total_engagement", "mean"),
        dominant_topic=("topic_label", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
    ).reset_index().rename(columns={"date": "date"})
    entity_ts.to_csv(OUT / "entity_timeseries.csv", index=False)

    platform = posts.groupby(["platform", "source_group"]).agg(
        n_records=("post_id", "count"),
        min_date=("date", "min"),
        max_date=("date", "max"),
    ).reset_index()
    platform["available_fields"] = "date,text,entity,sentiment,engagement,topic"
    platform["has_sentiment"] = True
    platform["has_topic"] = True
    platform["has_engagement"] = True
    platform.to_csv(OUT / "platform_summary.csv", index=False)

    events = trial_events()
    events.to_csv(OUT / "trial_events.csv", index=False)
    if errors:
        pd.DataFrame(errors).to_csv(OUT / "ingestion_warnings.csv", index=False)
    print(f"Wrote {len(posts):,} real processed records from {len(frames)} source files.")
    print(f"ThuggerDaily rows: {len(thugger):,}")
    print(f"Outputs: {OUT}")


if __name__ == "__main__":
    main()
