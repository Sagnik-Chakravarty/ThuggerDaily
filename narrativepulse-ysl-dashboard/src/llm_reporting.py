import requests
import pandas as pd

OLLAMA_URL = "http://localhost:11434"


def check_ollama_available(timeout=1.5) -> bool:
    try:
        return requests.get(f"{OLLAMA_URL}/api/tags", timeout=timeout).ok
    except requests.RequestException:
        return False


def list_ollama_models():
    if not check_ollama_available():
        return []
    try:
        data = requests.get(f"{OLLAMA_URL}/api/tags", timeout=3).json()
        return [m["name"] for m in data.get("models", [])]
    except requests.RequestException:
        return []


def build_report_prompt(report_type, metrics, events, examples=None):
    examples = examples or []
    return f"""
You are summarizing aggregate public discourse metrics.
Do not infer guilt, innocence, or legal truth.
Distinguish observed association from causation.
Use neutral, professional language.

Report type: {report_type}

Aggregate metrics:
{metrics}

Event timeline:
{events}

Selected example posts, if any:
{examples}

Write a concise professional report with uncertainty and limitations.
"""


def call_ollama(prompt, model="llama3.1"):
    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={"model": model, "prompt": prompt, "stream": False},
        timeout=60,
    )
    response.raise_for_status()
    return response.json().get("response", "")


def generate_template_report(report_type, metrics: pd.DataFrame, events: pd.DataFrame) -> str:
    metric_text = metrics.head(8).to_markdown(index=False) if hasattr(metrics, "to_markdown") else str(metrics)
    event_text = events.head(6).to_markdown(index=False) if hasattr(events, "to_markdown") else str(events)
    return (
        f"## {report_type.title()}\n\n"
        "This template report summarizes aggregate public discourse metrics. The visible pattern should be read as "
        "observational evidence of public narrative response, not proof of legal truth or definitive causality.\n\n"
        f"### Metric Snapshot\n{metric_text}\n\n"
        f"### Timeline Markers\n{event_text}\n\n"
        "### Limitations\nPlatform coverage, scraping/API limits, missing engagement denominators, slang, sarcasm, and omitted events can affect interpretation."
    )


def generate_llm_report(report_type, metrics, events, model="llama3.1", examples=None):
    if not check_ollama_available():
        return generate_template_report(report_type, metrics, events), False
    prompt = build_report_prompt(report_type, metrics, events, examples)
    try:
        return call_ollama(prompt, model=model), True
    except requests.RequestException:
        return generate_template_report(report_type, metrics, events), False
