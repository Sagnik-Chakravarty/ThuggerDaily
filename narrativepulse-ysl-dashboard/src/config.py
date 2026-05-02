from pathlib import Path

APP_NAME = "NarrativePulse"
APP_TITLE = "NarrativePulse: Public Narrative Analytics Dashboard"
BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
PROCESSED_DIR = DATA_DIR / "processed"
SAMPLE_DIR = DATA_DIR / "sample"

ENTITIES = ["Young Thug", "Gunna", "YFN Lucci"]
PLATFORMS = ["X/Twitter", "Reddit", "YouTube", "Instagram", "Google Trends", "Spotify", "Billboard", "Newspapers", "Magazines", "Local News"]
TOPICS = [
    "Live Music in Atlanta",
    "Slang",
    "Trial-related Content",
    "Legal System and Judicial Process",
    "Music",
    "Social Media Slang and Emojis",
    "Free Thug Support",
]

TOPIC_LEVEL_MAP = {
    "Live Music in Atlanta": ("local Atlanta culture", "local venue/music scene", "atlanta, venue, show, stage"),
    "Slang": ("slang/social media", "social media slang", "slang, phrase, reaction"),
    "Trial-related Content": ("legal", "trial/legal process", "trial, court, testimony"),
    "Legal System and Judicial Process": ("legal", "trial/legal process", "judge, motion, plea"),
    "Music": ("music", "music releases", "album, song, chart"),
    "Social Media Slang and Emojis": ("slang/social media", "social media slang", "emoji, meme, viral"),
    "Free Thug Support": ("fandom/support", "Free Thug support", "support, free, fan"),
}

CAUSAL_CAVEAT = (
    "This dashboard measures observational public narrative signals. It estimates temporal association, "
    "event-linked discourse shifts, and influence signals; it does not prove legal truth or randomized causal effects."
)
