from __future__ import annotations

from pathlib import Path
import textwrap
import numpy as np
import pandas as pd

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data" / "processed"
REPORTS = ROOT / "reports"
FIG = REPORTS / "figures_png"
TABLES = REPORTS / "tables"
TEX_PATH = REPORTS / "narrativepulse_thuggerdaily_trial_report.tex"


def esc(value) -> str:
    text = "" if pd.isna(value) else str(value)
    replacements = {
        "\\": r"\textbackslash{}",
        "&": r"\&",
        "%": r"\%",
        "$": r"\$",
        "#": r"\#",
        "_": r"\_",
        "{": r"\{",
        "}": r"\}",
        "~": r"\textasciitilde{}",
        "^": r"\textasciicircum{}",
    }
    for old, new in replacements.items():
        text = text.replace(old, new)
    return text


def savefig(name):
    path = FIG / name
    plt.tight_layout()
    plt.savefig(path, dpi=220, bbox_inches="tight")
    plt.close()
    return path


def latex_table(df: pd.DataFrame, columns, caption: str, label: str, max_rows=12, precision=3) -> str:
    view = df.loc[:, columns].head(max_rows).copy()
    for col in view.columns:
        if pd.api.types.is_numeric_dtype(view[col]):
            view[col] = view[col].map(lambda x: "" if pd.isna(x) else f"{x:,.{precision}f}")
        elif pd.api.types.is_datetime64_any_dtype(view[col]):
            view[col] = view[col].dt.strftime("%Y-%m-%d")
        else:
            view[col] = view[col].map(esc)
    colspec = "p{0.18\\linewidth}" * len(columns)
    rows = [" & ".join(esc(c).replace("\\_", " ") for c in columns) + r" \\"]
    rows.append(r"\midrule")
    for _, row in view.iterrows():
        rows.append(" & ".join(str(row[c]) for c in columns) + r" \\")
    return rf"""
\begin{{table}}[H]
\centering
\caption{{{esc(caption)}}}
\label{{{label}}}
\small
\begin{{tabular}}{{{colspec}}}
\toprule
{chr(10).join(rows)}
\bottomrule
\end{{tabular}}
\end{{table}}
"""


def pct(x):
    return "n/a" if pd.isna(x) else f"{x:.1f}\\%"


def main():
    FIG.mkdir(parents=True, exist_ok=True)
    TABLES.mkdir(parents=True, exist_ok=True)

    posts = pd.read_csv(DATA / "posts_master.csv", parse_dates=["date"])
    td = pd.read_csv(DATA / "thuggerdaily_posts.csv", parse_dates=["date"])
    events = pd.read_csv(TABLES / "key_trial_events.csv", parse_dates=["date"])
    coverage = pd.read_csv(TABLES / "coverage_by_platform_entity.csv", parse_dates=["min_date", "max_date"])
    event_results = pd.read_csv(TABLES / "thuggerdaily_event_window_results_7d.csv", parse_dates=["event_date"])
    young = pd.read_csv(TABLES / "young_thug_key_event_summary.csv", parse_dates=["event_date"])
    lag = pd.read_csv(TABLES / "lag_correlation_results.csv")
    topic = pd.read_csv(TABLES / "young_thug_topic_shift_results.csv")

    total_records = len(posts)
    td_records = len(td)
    platform_count = posts["platform"].nunique()
    entity_count = posts["entity"].nunique()
    topic_count = posts["topic_label"].nunique()
    date_min = posts["date"].min().date()
    date_max = posts["date"].max().date()
    entity_counts = posts["entity"].value_counts()
    platform_counts = posts["platform"].value_counts()

    # Figure 1: platform/entity records.
    pivot = posts.groupby(["platform", "entity"]).size().unstack(fill_value=0).loc[platform_counts.index]
    ax = pivot.plot(kind="bar", stacked=True, figsize=(10, 5.5), color=["#2563eb", "#ef4444", "#10b981"])
    ax.set_title("Cross-Platform Records by Entity")
    ax.set_xlabel("Platform")
    ax.set_ylabel("Records")
    ax.legend(title="Entity", fontsize=8)
    plt.xticks(rotation=35, ha="right")
    fig_platform = savefig("fig01_records_by_platform_entity.png")

    # Figure 2: public volume timeline.
    daily = posts.groupby("date").size().rename("records").reset_index()
    daily["records_14d"] = daily["records"].rolling(14, min_periods=1).mean()
    plt.figure(figsize=(11, 4.8))
    plt.plot(daily["date"], daily["records_14d"], color="#2563eb", linewidth=1.6)
    for _, row in events[events["event_id"].isin(["indictment_arrests", "gunna_release", "lyrics_evidence", "opening_statements", "glanville_recused", "young_thug_plea", "trial_end"])].iterrows():
        plt.axvline(row["date"], color="#64748b", linestyle="--", linewidth=0.8)
    plt.title("14-Day Smoothed Public Discourse Volume with Trial Events")
    plt.xlabel("Date")
    plt.ylabel("Records per day")
    fig_volume = savefig("fig02_public_volume_timeline.png")

    # Figure 3: sentiment trend.
    sent = posts.groupby(["date", "entity"])["sentiment_score"].mean().reset_index()
    sent["sentiment_14d"] = sent.groupby("entity")["sentiment_score"].transform(lambda s: s.rolling(14, min_periods=3).mean())
    plt.figure(figsize=(11, 5))
    for entity, group in sent.groupby("entity"):
        plt.plot(group["date"], group["sentiment_14d"], label=entity, linewidth=1.3)
    for _, row in events[events["event_id"].isin(["lyrics_evidence", "opening_statements", "glanville_recused", "young_thug_plea", "trial_end"])].iterrows():
        plt.axvline(row["date"], color="#94a3b8", linestyle="--", linewidth=0.8)
    plt.axhline(0, color="#111827", linewidth=0.6)
    plt.title("14-Day Smoothed Public Sentiment by Entity")
    plt.xlabel("Date")
    plt.ylabel("Mean sentiment")
    plt.legend()
    fig_sentiment = savefig("fig03_sentiment_by_entity.png")

    # Figure 4: ThuggerDaily posting.
    td_daily = td.groupby("date").agg(posts=("post_id", "count"), engagement=("total_engagement", "sum")).reset_index()
    plt.figure(figsize=(11, 4.8))
    plt.bar(td_daily["date"], td_daily["posts"], color="#0f766e", width=1.5)
    for _, row in events[events["event_id"].isin(["lyrics_evidence", "opening_statements", "glanville_recused", "young_thug_plea", "trial_end"])].iterrows():
        plt.axvline(row["date"], color="#64748b", linestyle="--", linewidth=0.8)
    plt.title("ThuggerDaily Posting Volume Over the Trial Timeline")
    plt.xlabel("Date")
    plt.ylabel("Posts per day")
    fig_td = savefig("fig04_thuggerdaily_volume.png")

    # Figure 5: event sentiment change.
    subset = event_results[event_results["entity"].isin(["Young Thug", "Gunna", "YFN Lucci"])].copy()
    event_order = list(dict.fromkeys(subset["event_name"]))
    x = np.arange(len(event_order))
    width = 0.25
    plt.figure(figsize=(12, 6))
    for i, entity in enumerate(["Young Thug", "Gunna", "YFN Lucci"]):
        vals = subset[subset["entity"].eq(entity)].set_index("event_name").reindex(event_order)["sentiment_change"]
        plt.bar(x + (i - 1) * width, vals, width=width, label=entity)
    plt.axhline(0, color="#111827", linewidth=0.7)
    plt.xticks(x, [e[:28] + ("..." if len(e) > 28 else "") for e in event_order], rotation=35, ha="right")
    plt.title("Seven-Day Pre/Post Sentiment Change Around Key Events")
    plt.ylabel("Post minus pre mean sentiment")
    plt.legend()
    fig_event_sent = savefig("fig05_event_sentiment_change.png")

    # Figure 6: event volume change for Young Thug.
    yv = young.sort_values("event_date")
    plt.figure(figsize=(11, 5.5))
    colors = ["#16a34a" if v >= 0 else "#dc2626" for v in yv["volume_change"]]
    plt.barh(yv["event_name"], yv["volume_change"], color=colors)
    plt.axvline(0, color="#111827", linewidth=0.7)
    plt.title("Young Thug Seven-Day Public Volume Change Around Key Events")
    plt.xlabel("Post-window records minus pre-window records")
    fig_volume_change = savefig("fig06_young_thug_volume_change.png")

    # Figure 7: lag correlations.
    plt.figure(figsize=(9, 5))
    for col in [c for c in lag.columns if c != "lag_days"]:
        plt.plot(lag["lag_days"], lag[col], marker="o", label=col.replace("_", " "))
    plt.axhline(0, color="#111827", linewidth=0.7)
    plt.title("Exploratory Lag Correlations")
    plt.xlabel("Lag days")
    plt.ylabel("Correlation")
    plt.legend(fontsize=7)
    fig_lag = savefig("fig07_lag_correlations.png")

    # Figure 8: topic shift around plea.
    plea_topic = topic[topic["event_id"].eq("young_thug_plea")].sort_values("share_change")
    plt.figure(figsize=(9, 5))
    plt.barh(plea_topic["topic_label"], plea_topic["share_change"], color="#7c3aed")
    plt.axvline(0, color="#111827", linewidth=0.7)
    plt.title("Topic Share Shift Around Young Thug Plea / Release")
    plt.xlabel("Post minus pre topic share")
    fig_topic = savefig("fig08_topic_shift_plea.png")

    # Figure 9: ThuggerDaily aligned share for Young Thug events.
    plt.figure(figsize=(11, 5.5))
    aligned = yv.copy()
    vals = aligned["sentiment_shift_aligned_share"].replace([np.inf, -np.inf], np.nan).clip(-200, 200)
    colors = ["#16a34a" if pd.notna(v) and v >= 0 else "#dc2626" for v in vals]
    plt.barh(aligned["event_name"], vals, color=colors)
    plt.axvline(0, color="#111827", linewidth=0.7)
    plt.title("ThuggerDaily-Aligned Share of Sentiment Shift (Capped for Display)")
    plt.xlabel("Aligned share of observed sentiment shift (%)")
    fig_attr = savefig("fig09_attribution_share.png")

    top_event = young.sort_values("td_post_posts", ascending=False).iloc[0]
    plea = young[young["event_name"].str.contains("pleads guilty", case=False, na=False)].iloc[0]
    recusal = young[young["event_name"].str.contains("Glanville", case=False, na=False)].iloc[0]
    opening = young[young["event_name"].str.contains("Opening", case=False, na=False)].iloc[0]

    tables = {
        "coverage": latex_table(
            coverage.sort_values("n_records", ascending=False),
            ["platform", "entity", "n_records", "mean_sentiment", "total_engagement"],
            "Coverage by platform and entity, sorted by record count.",
            "tab:coverage",
            max_rows=14,
        ),
        "events": latex_table(
            events,
            ["date", "event_name", "entity", "event_type", "source"],
            "Key trial and media events used in the event-window design.",
            "tab:events",
            max_rows=20,
        ),
        "young": latex_table(
            young.sort_values("event_date"),
            ["event_date", "event_name", "pre_records", "post_records", "volume_change", "sentiment_change", "td_post_posts", "td_post_engagement"],
            "Young Thug event-window summary with ThuggerDaily post-window exposure.",
            "tab:young_event_summary",
            max_rows=10,
        ),
        "lag": latex_table(
            lag,
            ["lag_days", "corr_td_posts_public_volume", "corr_td_engagement_public_volume", "corr_td_posts_sentiment", "corr_td_posts_public_engagement"],
            "Exploratory lag correlations between ThuggerDaily activity and downstream public metrics.",
            "tab:lag",
            max_rows=10,
        ),
    }

    body = rf"""
\documentclass[12pt]{{article}}
\usepackage[margin=0.9in]{{geometry}}
\usepackage{{graphicx}}
\usepackage{{booktabs}}
\usepackage{{float}}
\usepackage{{longtable}}
\usepackage{{array}}
\usepackage{{setspace}}
\usepackage{{titlesec}}
\usepackage{{hyperref}}
\usepackage{{xcolor}}
\usepackage{{caption}}
\usepackage{{enumitem}}
\usepackage{{amsmath}}
\usepackage{{fancyhdr}}
\hypersetup{{colorlinks=true, linkcolor=blue, urlcolor=blue, citecolor=blue}}
\setstretch{{1.18}}
\pagestyle{{fancy}}
\fancyhf{{}}
\lhead{{NarrativePulse}}
\rhead{{ThuggerDaily Trial Narrative Analysis}}
\cfoot{{\thepage}}
\titleformat{{\section}}{{\Large\bfseries}}{{\thesection}}{{0.7em}}{{}}
\titleformat{{\subsection}}{{\large\bfseries}}{{\thesubsection}}{{0.7em}}{{}}

\title{{\textbf{{NarrativePulse: ThuggerDaily and the YSL Trial}}\\
\large Event-Linked Public Narrative Analytics, Sentiment Dynamics, and Observational Influence Signals}}
\author{{Prepared from the NarrativePulse Dashboard Data Pipeline}}
\date{{May 2026}}

\begin{{document}}
\maketitle
\begin{{abstract}}
This report examines whether ThuggerDaily's X/Twitter posting activity was temporally associated with measurable shifts in public discourse around the Young Thug / YSL RICO trial. The analysis uses a unified processed corpus of {total_records:,} public records from {platform_count} platforms, including {td_records:,} ThuggerDaily records, spanning {date_min} through {date_max}. The central object is not legal truth, guilt, innocence, or judicial causation. It is public narrative response: volume, sentiment, engagement, topic prevalence, and the timing of cross-platform attention. The empirical strategy combines event-window analysis, lag correlation, topic-shift analysis, and a ThuggerDaily-aligned attribution signal that compares post-event public outcomes on days with and without observed ThuggerDaily exposure. Results support the presence of event-linked discourse shifts and platform-level attention patterns, but they do not prove randomized causal effects. The most defensible interpretation is that ThuggerDaily supplied a visible, recurring amplification channel whose activity sometimes coincided with downstream movement in public attention and sentiment, especially around high-salience legal moments.
\end{{abstract}}

\newpage
\tableofcontents
\newpage

\section{{Executive Summary}}
NarrativePulse was built to convert a broad public-data project into a professional legal-media intelligence dashboard. The motivating question is whether a single high-visibility X/Twitter account, ThuggerDaily, appeared to influence public discourse surrounding the YSL RICO trial. The account is treated as an observable exposure source. Trial events are treated as shocks to public attention. Downstream public reaction is measured across YouTube, X/Twitter, magazines, local news, newspapers, Spotify, Billboard, and Instagram.

The processed dashboard corpus contains \textbf{{{total_records:,}}} records, \textbf{{{td_records:,}}} of which are ThuggerDaily posts. Entity coverage is distributed across Young Thug ({entity_counts.get('Young Thug', 0):,} records), Gunna ({entity_counts.get('Gunna', 0):,} records), and YFN Lucci ({entity_counts.get('YFN Lucci', 0):,} records). The largest source in the unified corpus is YouTube, followed by X/Twitter and media sources. This platform imbalance matters: YouTube comments and video statistics dominate the count distribution, while ThuggerDaily itself is concentrated on X/Twitter.

The report's core finding is careful but meaningful: public discourse did shift around major trial dates, and ThuggerDaily activity often appeared near the same windows. However, the strongest valid claim is an \emph{{influence signal}}, not proof of causal responsibility. Around the Young Thug plea and release event on October 31, 2024, the seven-day event window showed a change in observed public attention and sentiment, while ThuggerDaily posted in the same post-event period. Around procedural shocks such as Judge Ural Glanville's recusal, public discourse also moved, but the amount plausibly attributable to ThuggerDaily depends strongly on platform coverage and denominator assumptions.

This distinction is essential. Trial outcomes are produced by legal institutions, filings, courtroom decisions, counsel strategy, plea negotiations, and judicial process. Social media can shape public narrative, amplify interpretations, and change what audiences notice, but this dataset cannot identify a randomized causal pathway from tweet to court outcome. The phrase ``affected the trial'' is therefore interpreted here as: \emph{{affected the public narrative around the trial, and potentially the public-facing information environment in which the trial was discussed.}}

\section{{Research Question and Product Framing}}
\subsection{{Primary Question}}
How did ThuggerDaily's X/Twitter posts temporally align with public sentiment, engagement, topic prevalence, and discourse volume around Young Thug, Gunna, and YFN Lucci across platforms?

\subsection{{Interpretive Boundary}}
The analysis avoids the claim that ThuggerDaily caused legal outcomes. Instead, it estimates:
\begin{{itemize}}[leftmargin=*]
\item temporal association between ThuggerDaily posts and downstream public discourse;
\item event-linked discourse shifts around trial dates;
\item platform-level public reaction after salient legal events;
\item topic and sentiment movement in windows surrounding observed exposure.
\end{{itemize}}

The central inferential challenge is confounding. Major courtroom events and ThuggerDaily posts often occur in the same period because both respond to the same underlying news. A spike in public discourse after a plea, for example, may be caused by the plea itself, by mainstream media coverage, by courtroom livestream clips, by ThuggerDaily, by fan communities, or by all of these forces interacting. The report therefore treats ThuggerDaily as one visible node in a broader public attention system.

\section{{Data and Source Coverage}}
The processed dataset was generated from the existing project folders under \texttt{{Data/Cleaned Data}}. Source-specific cleaned exports were standardized into the dashboard schema by \texttt{{scripts/build\_processed\_data.py}}. Each record was assigned a platform, source group, date, text field, entity, engagement fields where available, sentiment score, sentiment label, topic label, and topic levels.

The real processed corpus spans {date_min} through {date_max}. It includes {platform_count} platforms and {topic_count} generalized topic groups. The resulting platform distribution is not balanced. This is not a flaw; it is a property of the public record that must be interpreted honestly. Platforms differ in sampling method, API availability, comment density, engagement denominators, and whether the source is a user-generated stream, a video platform, a newspaper article, a chart record, or a music metadata source.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_platform.relative_to(REPORTS).as_posix()}}}
\caption{{Cross-platform record coverage by entity. YouTube dominates the unified record count, which means raw volume should be interpreted alongside platform-specific views.}}
\label{{fig:coverage}}
\end{{figure}}

{tables['coverage']}

\newpage
\section{{Trial Timeline and External Validation}}
The event table was built from the local \texttt{{Young Thug Time Line.rtf}} file and cross-checked against public reporting. The indictment and early bond events are consistent with public timelines such as Hip Hop History's YSL trial chronology.\footnote{{Hip Hop History, ``A Timeline of Young Thug and YSL's Atlanta RICO Trial,'' \url{{https://history.hiphop/young-thug-trial-timeline/}}.}} The November 9, 2023 lyrics ruling is supported by Pitchfork reporting.\footnote{{Pitchfork, ``Young Thug's Lyrics Can be Entered as Evidence in YSL RICO Trial, Judge Rules,'' \url{{https://pitchfork.com/news/young-thug-lyrics-can-be-entered-as-evidence-in-ysl-rico-trial-judge-rules/}}.}} Opening statements on November 27, 2023 are documented by The FADER.\footnote{{The FADER, ``Prosecutor quotes The Jungle Book, reads Young Thug lyrics in YSL trial opening statement,'' \url{{https://www.thefader.com/2023/11/27/prosecutor-quotes-the-jungle-book-reads-young-thug-lyrics-in-ysl-trial-opening-statement}}.}} Judge Glanville's July 15, 2024 recusal is reported by the Los Angeles Times.\footnote{{Los Angeles Times, ``Judge in Young Thug RICO case recused as YSL trial in Atlanta goes on hold indefinitely,'' \url{{https://www.latimes.com/entertainment-arts/music/story/2024-07-15/ysl-trial-young-thug-judge-recused-ural-glanville-rico}}.}} Young Thug's October 31, 2024 plea is documented by NPR.\footnote{{NPR, ``Young Thug pleads guilty in YSL trial, will serve probation,'' \url{{https://www.npr.org/2024/10/31/nx-s1-5174207/young-thug-guilty-plea-ysl-trial}}.}} The December 3, 2024 end of the trial for remaining defendants is reported by the Los Angeles Times.\footnote{{Los Angeles Times, ``YSL RICO trial ends,'' \url{{https://www.latimes.com/entertainment-arts/music/story/2024-12-03/ysl-rico-trial-ends-defendants-not-guilty-young-thug}}.}}

{tables['events']}

\section{{Methodology}}
\subsection{{Unified Record Construction}}
The ingestion script reads cleaned source exports from social media, video, news, music, and chart folders. Because the original files have source-specific schemas, the adapter detects likely date, text, engagement, URL, author, and keyword fields. Entity assignment is based on explicit references to Young Thug, Gunna, YFN Lucci, or close aliases in text and keyword fields. This method is transparent and reproducible, but it is not perfect. It can over-assign YSL-related records to Young Thug when a source talks broadly about the case.

\subsection{{Sentiment}}
Sentiment is scored as a lightweight public-language signal. The score is not treated as a psychological measure. Slang, sarcasm, legal vocabulary, fan language, and hip-hop discourse can all create misclassification. The report therefore emphasizes changes across time and groups rather than the absolute meaning of any individual score.

\subsection{{Engagement}}
Engagement is defined as:
\[
\text{{Engagement Rate}} = \frac{{\text{{Likes}} + \text{{Retweets}} + \text{{Comments}}}}{{\text{{Analytics}}}} \times 100.
\]
When a denominator is missing, the dashboard preserves raw engagement counts. For non-X platforms, shares or available substitutes are used when retweets are unavailable. This enables broad comparison while preserving a warning: engagement fields are not semantically identical across platforms.

\subsection{{Topic Leveling}}
The project uses seven generalized topics: Live Music in Atlanta, Slang, Trial-related Content, Legal System and Judicial Process, Music, Social Media Slang and Emojis, and Free Thug Support. These are mapped into broader interpretive levels: legal, music, fandom/support, slang/social media, media/news, and local Atlanta culture.

\subsection{{Event-Window Design}}
For each key date, the notebook estimates seven-day pre/post changes:
\[
\Delta_y = \bar{{Y}}_{{post}} - \bar{{Y}}_{{pre}}.
\]
Outcomes include public volume, sentiment, engagement, and topic shares. The event-window output is descriptive and observational.

\subsection{{ThuggerDaily-Aligned Attribution Signal}}
The attribution-style signal asks: within the post-event window, are public outcomes different on days when ThuggerDaily posted compared with days when it did not? Formally, for an outcome \(Y\):
\[
\text{{Exposure Lift}} = \bar{{Y}}_{{post, TD>0}} - \bar{{Y}}_{{post, TD=0}}.
\]
The aligned share compares this lift to the observed event-window shift:
\[
\text{{Aligned Share}} = \frac{{\text{{Exposure Lift}}}}{{\Delta_y}}.
\]
This quantity is not causal responsibility. It is a timing-based influence signal. It is best read as: ``how much of the observed movement is directionally aligned with ThuggerDaily exposure days?''

\newpage
\section{{Public Discourse Volume Over Time}}
The volume timeline shows bursts of public discourse around the trial's most visible moments. A highly publicized legal event can drive attention directly through news media, indirectly through social media recirculation, and recursively through fan or critic interpretation. ThuggerDaily's role is most visible when its posting clusters near these already salient events.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_volume.relative_to(REPORTS).as_posix()}}}
\caption{{Fourteen-day smoothed public discourse volume with selected key trial events marked by vertical dashed lines.}}
\label{{fig:volume}}
\end{{figure}}

The October 2024 plea period is especially important. The legal event itself is large enough to generate public attention independent of ThuggerDaily. The analytic question is therefore not whether ThuggerDaily created the moment, but whether it helped shape the public-facing interpretation of that moment. The data support the weaker and more credible claim: ThuggerDaily was active in the same information environment and its exposure days can be compared with non-exposure days for downstream public response.

\section{{Sentiment Dynamics}}
Sentiment trends differ by entity. Young Thug has the largest volume and, in many periods, the most sustained positive support signal, partly because fan-support narratives and ``Free Thug'' discourse are explicitly Young Thug-centered. Gunna's sentiment is more mixed around the plea period because public discourse includes loyalty, conflict, and accusation narratives. YFN Lucci appears at a lower volume, so estimates involving Lucci are less stable.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_sentiment.relative_to(REPORTS).as_posix()}}}
\caption{{Fourteen-day smoothed public sentiment by entity. The series should be interpreted as aggregate public-language tone, not ground truth public opinion.}}
\label{{fig:sentiment}}
\end{{figure}}

The sentiment pattern is not a simple linear story. Some legal shocks can raise supportive sentiment among fans while increasing negative legal commentary in news and comment spaces. This is why platform-level decomposition is necessary: the same event can generate sympathy on fan platforms, skepticism in comment sections, procedural discussion in news coverage, and music-driven attention on Spotify or Billboard.

\newpage
\section{{ThuggerDaily Activity as an Exposure Stream}}
ThuggerDaily is modeled as an exposure stream because its posts are observable, timestamped, and entity-linked. The account does not represent all public discourse, but it can act as a public-narrative amplifier. Its activity is especially relevant when it posts near major legal dates.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_td.relative_to(REPORTS).as_posix()}}}
\caption{{ThuggerDaily posting volume over the trial timeline, with selected major trial dates overlaid.}}
\label{{fig:tdvolume}}
\end{{figure}}

The strongest interpretation is that ThuggerDaily operates as a high-frequency public narrative node. When trial events occur, the account can select, frame, and amplify details. This selection function matters even when the underlying legal event is exogenous to the account. For example, a plea or recusal may happen for legal reasons, but public understanding of that event can be shaped by which clips, quotes, and reactions circulate.

\section{{Event-Window Results}}
The event-window analysis compares seven days before and seven days after each key event. Table \ref{{tab:young_event_summary}} reports Young Thug-focused windows, including public volume, sentiment movement, and ThuggerDaily post-window activity.

{tables['young']}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_event_sent.relative_to(REPORTS).as_posix()}}}
\caption{{Seven-day pre/post sentiment changes by entity. Positive values indicate higher post-event sentiment than pre-event sentiment.}}
\label{{fig:eventsent}}
\end{{figure}}

The event-window results show that public discourse shifts are not uniform. Some legal events generate increased volume but ambiguous sentiment changes. Others create sentiment changes without proportional volume growth. This supports a central product insight: the dashboard should not rely on a single KPI. Volume, sentiment, engagement, and topics are different dimensions of narrative reaction.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_volume_change.relative_to(REPORTS).as_posix()}}}
\caption{{Young Thug public volume change around key events. Green bars indicate post-window volume increases; red bars indicate decreases.}}
\label{{fig:volumechange}}
\end{{figure}}

\newpage
\section{{ThuggerDaily-Aligned Attribution}}
The attribution estimate is intentionally conservative. It does not say that ThuggerDaily ``caused'' a certain percent of the public shift. It says that the observed post-event shift can be compared with public outcomes on days where ThuggerDaily posted. If those days show higher public volume, stronger engagement, or different sentiment than non-exposure days, the report labels the result an aligned influence signal.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.98\linewidth]{{{fig_attr.relative_to(REPORTS).as_posix()}}}
\caption{{ThuggerDaily-aligned share of sentiment shift for Young Thug event windows. Values are capped for display because small denominators can inflate ratios.}}
\label{{fig:attr}}
\end{{figure}}

The top ThuggerDaily-exposed event window in the Young Thug summary was \textbf{{{esc(top_event['event_name'])}}}, with {int(top_event['td_post_posts'])} ThuggerDaily posts and {top_event['td_post_engagement']:,.0f} observed ThuggerDaily engagement in the post window. The Young Thug plea event showed a sentiment change of {plea['sentiment_change']:.3f} and a volume change of {plea['volume_change']:.0f} records in the seven-day design, with {int(plea['td_post_posts'])} ThuggerDaily post-window posts. The Glanville recusal event showed a sentiment change of {recusal['sentiment_change']:.3f}, while opening statements showed a sentiment change of {opening['sentiment_change']:.3f}.

These figures are meaningful because they show when the account's activity was present in the same short-run public attention window. They are limited because ThuggerDaily is not the only exposure. Courtroom livestreams, Law\&Crime clips, mainstream articles, Reddit discussions, Instagram posts, and artist/music events all contribute to the public information environment.

\section{{Lag Correlation}}
Lag correlations test whether ThuggerDaily activity predicts downstream public metrics after 0, 1, 3, 7, 14, or 30 days. Correlation is not causation, but it is useful for determining whether the relationship has plausible temporal ordering. If same-day correlation is high but longer lags are weak, the account may be reacting to the same event as everyone else. If post-day lags remain elevated, that suggests possible persistence or delayed amplification.

{tables['lag']}

\begin{{figure}}[H]
\centering
\includegraphics[width=0.88\linewidth]{{{fig_lag.relative_to(REPORTS).as_posix()}}}
\caption{{Exploratory lag correlations between ThuggerDaily posting/engagement and downstream public metrics.}}
\label{{fig:lag}}
\end{{figure}}

The lag analysis should be interpreted as a screening tool. A high lag correlation can motivate closer qualitative review of specific posts and downstream threads. It cannot isolate ThuggerDaily from other contemporaneous sources unless a stronger control strategy is added.

\newpage
\section{{Topic Movement}}
Topic movement helps explain \emph{{what kind}} of discourse changed. Trial events can shift attention toward legal procedure, support language, slang, music, or media coverage. Around the Young Thug plea and release, topic shifts reveal whether the public response was primarily legal, fan-supportive, music-related, or general social commentary.

\begin{{figure}}[H]
\centering
\includegraphics[width=0.88\linewidth]{{{fig_topic.relative_to(REPORTS).as_posix()}}}
\caption{{Topic share change around the Young Thug plea/release event.}}
\label{{fig:topicplea}}
\end{{figure}}

Topic shifts are especially important for legal-media intelligence because sentiment alone can hide the substantive change. A neutral sentiment score attached to legal-process language may still represent a major public-narrative shift if the conversation moves from music fandom to plea terms, judge behavior, witness credibility, or trial legitimacy.

\section{{Platform Interpretation}}
The platform composition affects every result. YouTube dominates raw records because video comments and video metadata are dense. X/Twitter is central to the ThuggerDaily exposure mechanism but is not the largest total record source. Magazines and newspapers provide fewer records but often contain higher-density narrative framing. Spotify and Billboard are not public-opinion platforms, but they provide music-attention signals around album releases and chart movement.

This multi-platform structure is a strength because it prevents the report from equating one platform with the public. It is also a limitation because measurement units differ. A YouTube comment, a tweet, a magazine article, and a Billboard chart row are not identical observations. The dashboard's role is to make these differences visible while still allowing an integrated public narrative view.

\section{{What Can Be Said About ``Affecting the Trial''}}
The phrase ``affected the trial'' needs a disciplined interpretation. Based on this dataset, the correct claim is not that ThuggerDaily altered a judge's ruling, changed a plea negotiation, or caused legal outcomes. The defensible claim is that ThuggerDaily appears to have affected the \emph{{public narrative environment around the trial}} by posting near key legal events and potentially amplifying selected frames.

Three mechanisms are plausible:
\begin{{enumerate}}[leftmargin=*]
\item \textbf{{Attention amplification:}} posts near legal events can increase the number of people who see or discuss the event.
\item \textbf{{Frame selection:}} the account can choose which aspects of courtroom activity become salient to followers.
\item \textbf{{Sentiment coordination:}} repeated support language can strengthen or concentrate fan sentiment around an entity.
\end{{enumerate}}

These mechanisms are media effects, not legal-causal proof. The report therefore uses the language of temporal association, influence signal, event-linked discourse shift, and public narrative response.

\newpage
\section{{Limitations}}
\subsection{{Observational Design}}
The analysis is observational. There is no randomized assignment of ThuggerDaily exposure. People who follow or react to ThuggerDaily are not randomly selected from the public. Trial events and posts may be jointly caused by the same news.

\subsection{{Omitted Confounders}}
The model does not fully observe all mainstream coverage, private group chats, TikTok, full X/Twitter firehose activity, courtroom livestream reach, or recommendation algorithm exposure. Omitted confounders can explain part of any observed association.

\subsection{{Platform Bias}}
The corpus is not platform-balanced. YouTube records dominate the sample. X/Twitter is central to the exposure but not the majority of downstream records. Platform-specific interpretation remains necessary.

\subsection{{Sentiment Error}}
Sentiment models can misread slang, sarcasm, legal terms, hip-hop discourse, and fan-coded language. Topic labels are useful abstractions but not perfect semantic truth.

\subsection{{Engagement Denominators}}
Engagement-rate denominators are inconsistent across sources. The dashboard uses analytics, impressions, or views where available and falls back to raw engagement where denominators are missing. This makes cross-platform engagement comparisons approximate.

\section{{Conclusion}}
The NarrativePulse analysis supports a nuanced conclusion. ThuggerDaily was not merely background noise: it was a measurable exposure stream with hundreds of posts in the trial-period corpus, and its activity often coincided with major legal events. Public discourse around the YSL RICO trial shifted in volume, sentiment, engagement, and topic composition around key dates. The account's post-window activity can be used to estimate aligned influence signals, especially when comparing public outcomes on exposure versus non-exposure days.

At the same time, the analysis does not prove that ThuggerDaily caused legal outcomes or singularly changed public opinion. The more rigorous conclusion is that ThuggerDaily likely contributed to the public narrative system surrounding the trial by amplifying attention, selecting frames, and concentrating fan/support discourse around Young Thug. In a legal-media intelligence setting, that is already a meaningful result: public legitimacy, reputational dynamics, and narrative momentum are not the same as courtroom facts, but they are measurable features of high-profile legal events.

\section{{Appendix A: Reproducibility}}
The report is generated from:
\begin{{itemize}}[leftmargin=*]
\item \texttt{{scripts/build\_processed\_data.py}} for standardized processed CSV generation;
\item \texttt{{notebooks/thuggerdaily\_trial\_effect\_report.ipynb}} for report-ready result tables and interactive charts;
\item \texttt{{scripts/generate\_latex\_report.py}} for this LaTeX manuscript and static PNG figures.
\end{{itemize}}

To regenerate:
\begin{{verbatim}}
cd narrativepulse-ysl-dashboard
source .venv/bin/activate
python scripts/build_processed_data.py
python scripts/generate_latex_report.py
\end{{verbatim}}

\section{{Appendix B: Ethical and Legal Communication Note}}
The dashboard and report should not be used to infer guilt, innocence, or legal truth. The data are public-discourse artifacts. They describe how public channels talked about the trial, not what happened in court as a matter of law. The strongest professional framing is public narrative analytics, legal-media intelligence, and observational event-linked discourse measurement.

\end{{document}}
"""

    TEX_PATH.write_text(textwrap.dedent(body).strip() + "\n", encoding="utf-8")
    print(f"Wrote {TEX_PATH}")
    print(f"Wrote figures to {FIG}")


if __name__ == "__main__":
    main()
