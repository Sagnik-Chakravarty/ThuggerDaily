import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

TEMPLATE = "plotly_white"
COLORS = px.colors.qualitative.Safe


def _empty(title="No data available"):
    fig = go.Figure()
    fig.update_layout(title=title, template=TEMPLATE, height=360)
    return fig


def line_sentiment_over_time(df):
    if df.empty:
        return _empty()
    return px.line(df, x="date", y="mean_sentiment", color="entity", line_dash="platform" if "platform" in df else None, template=TEMPLATE, title="Average Sentiment Over Time")


def line_volume_over_time(df):
    if df.empty:
        return _empty()
    y = "n_posts" if "n_posts" in df else "post_id"
    if y == "post_id":
        df = df.groupby("date").size().reset_index(name="n_posts")
        y = "n_posts"
    return px.line(df, x="date", y=y, color="entity" if "entity" in df else None, template=TEMPLATE, title="Public Discourse Volume Over Time")


def bar_records_by_platform(df):
    if "n_records" not in df:
        df = df.groupby("platform").size().reset_index(name="n_records")
    return px.bar(df.sort_values("n_records", ascending=False), x="platform", y="n_records", color="platform", template=TEMPLATE, title="Records by Platform")


def heatmap_platform_entity_sentiment(df):
    if df.empty:
        return _empty()
    pivot = df.pivot_table(index="platform", columns="entity", values="sentiment_score", aggfunc="mean")
    return px.imshow(pivot, text_auto=".2f", color_continuous_scale="RdBu", zmin=-1, zmax=1, template=TEMPLATE, title="Mean Sentiment by Platform and Entity")


def stacked_sentiment_share(df):
    if df.empty:
        return _empty()
    cols = [c for c in ["positive_share", "negative_share", "neutral_share"] if c in df]
    long = df.melt(id_vars=["date"], value_vars=cols, var_name="sentiment", value_name="share")
    return px.area(long, x="date", y="share", color="sentiment", template=TEMPLATE, title="Sentiment Share Over Time")


def topic_prevalence_area(df):
    if df.empty:
        return _empty()
    return px.area(df, x="date", y="topic_share", color="topic_label", template=TEMPLATE, title="Topic Prevalence Over Time")


def topic_heatmap(df):
    if df.empty:
        return _empty()
    pivot = df.pivot_table(index="topic_label", columns="platform", values="topic_share", aggfunc="mean").fillna(0)
    return px.imshow(pivot, text_auto=".1%", color_continuous_scale="Blues", template=TEMPLATE, title="Topic Distribution by Platform")


def engagement_spike_plot(df):
    if df.empty:
        return _empty()
    y = "total_engagement" if "total_engagement" in df else "likes"
    return px.scatter(df, x="date", y=y, color="entity", size=y, hover_data=["topic_label", "text"] if "text" in df else None, template=TEMPLATE, title="Engagement Spikes")


def event_study_plot(window_df, outcome):
    if window_df.empty:
        return _empty()
    fig = px.scatter(window_df, x="days_from_event", y=outcome, color="period", template=TEMPLATE, title="Event Window Outcome")
    fig.add_vline(x=0, line_dash="dash", line_color="black")
    return fig


def did_plot(table):
    if table is None or table.empty:
        return _empty()
    work = table.copy()
    work["group"] = work["treated"].map({1: "Treatment", 0: "Control"})
    work["period"] = work["post"].map({1: "Post", 0: "Pre"})
    return px.line(work, x="period", y="mean_outcome", color="group", markers=True, template=TEMPLATE, title="Difference-in-Differences Mean Outcome")


def lag_correlation_plot(df):
    if df.empty:
        return _empty()
    return px.bar(df, x="lag_days", y="correlation", template=TEMPLATE, title="Lag Correlation")


def missingness_heatmap(df):
    miss = df.isna().mean().to_frame("missing_rate").T
    return px.imshow(miss, text_auto=".0%", color_continuous_scale="Reds", template=TEMPLATE, title="Missingness by Field")


def engagement_denominator_coverage_plot(df):
    """
    Visual flag for cross-platform engagement-rate denominator differences.
    Bars show which denominator type is available per platform.
    """
    if df is None or df.empty or "platform" not in df:
        return _empty("No data available")
    analytics = pd.to_numeric(df.get("analytics", pd.Series(index=df.index, dtype=float)), errors="coerce").fillna(0)
    views = pd.to_numeric(df.get("views", pd.Series(index=df.index, dtype=float)), errors="coerce").fillna(0)
    denom = pd.Series("none", index=df.index, dtype=object)
    denom.loc[views > 0] = "views"
    denom.loc[analytics > 0] = "analytics"
    work = pd.DataFrame({"platform": df["platform"], "denominator_type": denom})
    out = work.groupby(["platform", "denominator_type"]).size().reset_index(name="n_records")
    total = out.groupby("platform")["n_records"].transform("sum").replace(0, pd.NA)
    out["share"] = out["n_records"] / total
    order = out.groupby("platform")["n_records"].sum().sort_values(ascending=False).index.tolist()
    fig = px.bar(
        out,
        x="platform",
        y="share",
        color="denominator_type",
        category_orders={"platform": order, "denominator_type": ["analytics", "views", "none"]},
        template=TEMPLATE,
        title="Engagement Denominator Coverage by Platform",
    )
    fig.update_yaxes(tickformat=".0%")
    fig.update_layout(legend_title_text="Denominator used")
    return fig
