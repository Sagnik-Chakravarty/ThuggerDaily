import streamlit as st
from .config import CAUSAL_CAVEAT
from .database import database_available
from .load_data import missing_processed_files


def apply_light_theme():
    st.markdown(
        """
        <style>
        :root, [data-testid="stAppViewContainer"] {
            color-scheme: light;
        }
        .stApp {
            background: #ffffff;
            color: #17202a;
        }
        [data-testid="stSidebar"] {
            background: #f6f8fb;
        }
        [data-testid="stMetric"] {
            background: #ffffff;
            border: 1px solid #e5e7eb;
            border-radius: 8px;
            padding: 14px 16px;
        }
        div[data-testid="stAlert"] {
            border-radius: 8px;
        }
        .np-note {
            border: 1px solid #d7dde8;
            background: #f8fafc;
            color: #334155;
            border-radius: 8px;
            padding: 12px 14px;
            margin: 12px 0 18px;
            font-size: 0.95rem;
        }
        .np-small {
            color: #64748b;
            font-size: 0.85rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_sidebar_filters(posts):
    st.sidebar.header("Filters")
    entities = ["all"] + sorted([x for x in posts["entity"].dropna().unique()])
    platforms = ["all"] + sorted([x for x in posts["platform"].dropna().unique()])
    entity = st.sidebar.selectbox("Entity", entities)
    platform = st.sidebar.selectbox("Platform", platforms)
    min_date = posts["date"].min().date()
    max_date = posts["date"].max().date()
    date_range = st.sidebar.date_input("Date range", (min_date, max_date), min_value=min_date, max_value=max_date)
    return {"entity": entity, "platform": platform, "date_range": date_range}


def apply_filters(posts, filters):
    df = posts.copy()
    if filters.get("entity") != "all":
        df = df[df["entity"] == filters["entity"]]
    if filters.get("platform") != "all":
        df = df[df["platform"] == filters["platform"]]
    date_range = filters.get("date_range")
    if isinstance(date_range, tuple) and len(date_range) == 2:
        start, end = date_range
        df = df[df["date"].dt.date.between(start, end)]
    return df


def render_kpi_cards(items):
    cols = st.columns(len(items))
    for col, (label, value, help_text) in zip(cols, items):
        col.metric(label, value, help=help_text)


def render_caveat_box(text=CAUSAL_CAVEAT):
    st.markdown(f"<div class='np-note'>{text}</div>", unsafe_allow_html=True)


def render_demo_mode_notice(required_files=None):
    if database_available():
        st.sidebar.caption("Data backend: Neon Postgres")
        return
    missing = missing_processed_files(required_files)
    if missing:
        st.sidebar.caption("Demo data active. Add processed CSVs to `data/processed/` to replace it.")


def render_model_summary(model, title: str):
    st.markdown(f"#### {title}")
    if model is None:
        st.caption("Model not fit because there were not enough observations, variation, or dependencies.")
        return
    params = getattr(model, "params", None)
    if params is None:
        st.caption("No model parameters available.")
        return
    table = params.reset_index()
    table.columns = ["term", "estimate"]
    if hasattr(model, "bse"):
        table["std_error"] = model.bse.values
    if hasattr(model, "pvalues"):
        table["p_value"] = model.pvalues.values
    try:
        ci = model.conf_int()
        table["ci_lower"] = ci.iloc[:, 0].values
        table["ci_upper"] = ci.iloc[:, 1].values
    except Exception:
        pass
    st.dataframe(table.round(4), use_container_width=True, hide_index=True)
    st.caption(f"Observations: {int(getattr(model, 'nobs', 0)):,}. Coefficients are exploratory associations, not proof of causation.")


def render_data_warning(message):
    st.warning(message)


def render_methodology_note():
    st.caption("Methods are designed for aggregate, processed, public, sampled, or anonymized data. Interpret outputs as public narrative signals.")
