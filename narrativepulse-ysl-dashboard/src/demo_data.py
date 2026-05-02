import numpy as np
import pandas as pd
from .config import ENTITIES, PLATFORMS, TOPICS, TOPIC_LEVEL_MAP
from .engagement import calculate_engagement_rate, calculate_total_engagement
from .preprocessing import assign_sentiment_label
from .topic_leveling import assign_topic_levels


EVENTS = [
    ("2022-05-09", "YSL indictment announced", "legal", "Young Thug"),
    ("2022-12-14", "Gunna plea and release", "legal", "Gunna"),
    ("2023-11-27", "Opening statements begin", "legal", "Young Thug"),
    ("2024-06-10", "High-visibility testimony period", "legal", "Young Thug"),
    ("2024-10-31", "Young Thug plea and release", "legal", "Young Thug"),
    ("2024-12-03", "Post-resolution media cycle", "media", "all"),
]


def _event_spike(date, events):
    return sum(max(0, 1 - abs((date - pd.Timestamp(e[0])).days) / 12) for e in events)


def create_demo_trial_events() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "event_id": f"evt_{i+1}",
                "date": d,
                "event_name": name,
                "event_type": typ,
                "entity": entity,
                "description": f"Timeline marker for {name}; used for event-linked discourse analysis.",
                "source": "Demo public timeline",
            }
            for i, (d, name, typ, entity) in enumerate(EVENTS)
        ]
    )


def create_demo_posts(n: int = 2600, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    dates = pd.date_range("2022-05-01", "2024-12-31", freq="D")
    event_dates = [(pd.Timestamp(d), name, typ, entity) for d, name, typ, entity in EVENTS]
    rows = []
    platform_probs = np.array([0.22, 0.18, 0.17, 0.12, 0.08, 0.06, 0.04, 0.06, 0.04, 0.03])
    for i in range(n):
        date = rng.choice(dates)
        spike = _event_spike(pd.Timestamp(date), event_dates)
        platform = rng.choice(PLATFORMS, p=platform_probs)
        entity = rng.choice(ENTITIES, p=[0.52, 0.30, 0.18])
        topic = rng.choice(TOPICS, p=[0.08, 0.10, 0.25, 0.17, 0.14, 0.10, 0.16])
        base_sentiment = {"Young Thug": 0.10, "Gunna": -0.02, "YFN Lucci": -0.04}[entity]
        topic_adj = {"Free Thug Support": 0.28, "Legal System and Judicial Process": -0.10, "Trial-related Content": -0.05, "Music": 0.18}.get(topic, 0)
        sentiment = np.clip(rng.normal(base_sentiment + topic_adj + 0.04 * spike, 0.35), -1, 1)
        impressions = int(rng.lognormal(8.0 + 0.45 * spike, 1.0))
        likes = int(impressions * rng.uniform(0.005, 0.055))
        comments = int(impressions * rng.uniform(0.001, 0.020))
        shares = int(impressions * rng.uniform(0.0005, 0.018))
        rows.append(
            {
                "post_id": f"demo_{i:05d}",
                "platform": platform,
                "date": pd.Timestamp(date).date().isoformat(),
                "text": f"Demo {platform} discourse about {entity}: {topic.lower()} around the YSL trial timeline.",
                "author": f"public_user_{rng.integers(1, 600)}",
                "entity": entity,
                "sentiment_score": sentiment,
                "sentiment_label": assign_sentiment_label(sentiment),
                "likes": likes,
                "comments": comments,
                "shares": shares,
                "retweets": shares if platform == "X/Twitter" else np.nan,
                "views": impressions if platform in ["YouTube", "Instagram", "X/Twitter"] else np.nan,
                "analytics": impressions if platform in ["X/Twitter", "YouTube"] else np.nan,
                "topic_id": TOPICS.index(topic) + 1,
                "topic_label": topic,
                "url": "",
            }
        )
    df = pd.DataFrame(rows)
    df = assign_topic_levels(df)
    df["total_engagement"] = calculate_total_engagement(df)
    df["engagement_rate"] = calculate_engagement_rate(df)
    return df.sort_values("date").reset_index(drop=True)


def create_demo_thuggerdaily_posts(n: int = 180, seed: int = 7) -> pd.DataFrame:
    posts = create_demo_posts(n=n, seed=seed)
    posts["platform"] = "X/Twitter"
    posts["author"] = "ThuggerDaily"
    posts["post_id"] = [f"td_{i:04d}" for i in range(len(posts))]
    posts["text"] = posts.apply(lambda r: f"Demo ThuggerDaily update mentioning {r['entity']} and {r['topic_label'].lower()}.", axis=1)
    return posts


def create_demo_topics() -> pd.DataFrame:
    posts = create_demo_posts(n=600, seed=11)
    cols = ["post_id", "date", "platform", "entity", "topic_id", "topic_label", "topic_level_1", "topic_level_2", "topic_level_3"]
    out = posts[cols].copy()
    out["top_keywords"] = out["topic_label"].map(lambda t: TOPIC_LEVEL_MAP.get(t, ("", "", "public, discourse"))[2])
    return out


def create_demo_all() -> dict[str, pd.DataFrame]:
    posts = create_demo_posts()
    td = create_demo_thuggerdaily_posts()
    events = create_demo_trial_events()
    topics = posts[["post_id", "date", "platform", "entity", "topic_id", "topic_label", "topic_level_1", "topic_level_2", "topic_level_3"]].copy()
    topics["top_keywords"] = topics["topic_level_3"]
    entity_ts = posts.groupby(["date", "platform", "entity"]).agg(
        n_posts=("post_id", "count"),
        mean_sentiment=("sentiment_score", "mean"),
        positive_share=("sentiment_label", lambda s: (s == "positive").mean()),
        negative_share=("sentiment_label", lambda s: (s == "negative").mean()),
        neutral_share=("sentiment_label", lambda s: (s == "neutral").mean()),
        total_engagement=("total_engagement", "sum"),
        mean_engagement=("total_engagement", "mean"),
        dominant_topic=("topic_label", lambda s: s.mode().iat[0] if not s.mode().empty else ""),
    ).reset_index()
    platform_summary = posts.groupby("platform").agg(
        n_records=("post_id", "count"),
        min_date=("date", "min"),
        max_date=("date", "max"),
    ).reset_index()
    platform_summary["source_group"] = platform_summary["platform"].map(lambda p: "social media" if p in ["X/Twitter", "Reddit", "Instagram"] else "media/search/music")
    platform_summary["available_fields"] = "date,text,entity,sentiment,engagement,topic"
    platform_summary["has_sentiment"] = True
    platform_summary["has_topic"] = True
    platform_summary["has_engagement"] = True
    return {
        "posts_master": posts,
        "thuggerdaily_posts": td,
        "trial_events": events,
        "topic_assignments": topics,
        "entity_timeseries": entity_ts,
        "platform_summary": platform_summary,
    }
