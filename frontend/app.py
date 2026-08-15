"""
Enterprise AI Research Agent -- Streamlit UI.

Design intent: this tool produces evidence, not chat replies. The UI is built
as a research dossier / intelligence dashboard -- numbered pipeline stages,
confidence-scored conclusions backed by data tables, classification charts --
deliberately not a chat-style scrolling summary. That distinction is the
actual point of the underlying assignment brief.

Talks to the FastAPI backend over HTTP (set BACKEND_URL in .env or Streamlit
secrets when deployed).
"""

import os
import time
import requests
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise AI Research Agent", layout="wide")


def api_get(path: str, params: dict | None = None):
    """GET wrapper that fails with a clear message instead of an unhandled
    traceback when the backend isn't reachable (e.g. it isn't running, or
    crashed) -- this is exactly the failure mode that previously surfaced as
    a raw ConnectionError stack trace in the UI."""
    try:
        r = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot reach the backend at {BACKEND_URL}. "
            f"Make sure it's running (`uvicorn backend.main:app --reload --port 8000`) and try again."
        )
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"Backend request failed: {e}")
        st.stop()


def api_post(path: str, json: dict):
    try:
        r = requests.post(f"{BACKEND_URL}{path}", json=json, timeout=10)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"Cannot reach the backend at {BACKEND_URL}. "
            f"Make sure it's running (`uvicorn backend.main:app --reload --port 8000`) and try again."
        )
        st.stop()
    except requests.exceptions.RequestException as e:
        st.error(f"Backend request failed: {e}")
        st.stop()


# --------------------------------------------------------------------------- design tokens / CSS
def inject_base_styles():
    st.markdown(
        """
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link href="https://fonts.googleapis.com/css2?family=Source+Serif+4:wght@500;600;700&family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500;600&display=swap" rel="stylesheet">
        <style>
        :root {
            --ink: #14181F;
            --paper: #F5F6F4;
            --panel: #FFFFFF;
            --border: #DFE2DF;
            --muted: #6B7280;
            --accent: #1F4B4C;
            --accent-light: #E6EDEC;
            --corroborated: #2F6E4F;
            --corroborated-bg: #EAF3EC;
            --contested: #A13D3D;
            --contested-bg: #F7EAE9;
            --single: #8A6B2A;
            --single-bg: #F5EFE0;
        }

        html, body, [class*="css"]  { font-family: 'IBM Plex Sans', sans-serif; color: var(--ink); }
        .stApp { background-color: var(--paper); }

        h1, h2, h3 { font-family: 'Source Serif 4', serif !important; font-weight: 600 !important; color: var(--ink) !important; }

        .app-header { border-bottom: 1px solid var(--border); padding-bottom: 1.1rem; margin-bottom: 1.6rem; }
        .app-title { font-family: 'Source Serif 4', serif; font-size: 2.0rem; font-weight: 700; margin: 0; color: var(--ink); }
        .app-subtitle { font-family: 'IBM Plex Mono', monospace; font-size: 0.82rem; color: var(--muted); margin-top: 4px; letter-spacing: 0.02em; }

        .badge { display: inline-block; padding: 2px 10px; border-radius: 3px; font-family: 'IBM Plex Mono', monospace;
                 font-size: 0.72rem; font-weight: 600; letter-spacing: 0.03em; text-transform: uppercase; white-space: nowrap; }
        .badge-corroborated { background: var(--corroborated-bg); color: var(--corroborated); border: 1px solid var(--corroborated); }
        .badge-contested { background: var(--contested-bg); color: var(--contested); border: 1px solid var(--contested); }
        .badge-single_source { background: var(--single-bg); color: var(--single); border: 1px solid var(--single); }
        .badge-domain { background: var(--accent-light); color: var(--accent); border: 1px solid var(--accent); }

        .metric-row { display: flex; gap: 12px; margin: 0.6rem 0 1.6rem 0; flex-wrap: wrap; }
        .metric-card { flex: 1; min-width: 130px; background: var(--panel); border: 1px solid var(--border);
                        border-radius: 4px; padding: 14px 16px; }
        .metric-value { font-family: 'IBM Plex Mono', monospace; font-size: 1.6rem; font-weight: 600; color: var(--ink); line-height: 1; }
        .metric-label { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.05em; margin-top: 6px; }

        .stepper-wrap { position: relative; padding: 0.6rem 2% 0.2rem 2%; margin-bottom: 0.6rem; }
        .stepper { display: flex; justify-content: space-between; position: relative; z-index: 2; }
        .step { flex: 1; text-align: center; }
        .step-circle { width: 34px; height: 34px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
                        margin: 0 auto 8px auto; font-family: 'IBM Plex Mono', monospace; font-weight: 600; font-size: 0.85rem;
                        border: 2px solid var(--border); background: var(--panel); color: var(--muted); }
        .step.done .step-circle { background: var(--accent); border-color: var(--accent); color: #fff; }
        .step.active .step-circle { border-color: var(--accent); color: var(--accent); box-shadow: 0 0 0 3px var(--accent-light); }
        .step-label { font-size: 0.76rem; color: var(--ink); font-weight: 500; }
        .step-sub { font-size: 0.68rem; color: var(--muted); margin-top: 2px; font-family: 'IBM Plex Mono', monospace; min-height: 14px; }
        .stepper-line-base { position: absolute; top: 33px; left: 7%; right: 7%; height: 2px; background: var(--border); z-index: 1; }
        .stepper-line-progress { position: absolute; top: 33px; left: 7%; height: 2px; background: var(--accent); z-index: 1; transition: width 0.3s ease; }

        .concl-index { font-family: 'IBM Plex Mono', monospace; color: var(--accent); font-size: 0.8rem; font-weight: 600; }
        .concl-text { font-size: 1.02rem; font-weight: 500; margin: 4px 0 10px 0; line-height: 1.45; }

        div[data-testid="stExpander"] { border: 1px solid var(--border); border-radius: 4px; background: var(--panel); }
        </style>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- small components
PIPELINE_STAGES = [
    {"key": "classify", "num": "01", "label": "Classify & Plan", "event_stages": {"classify"}},
    {"key": "search", "num": "02", "label": "Search & Collect", "event_stages": {"search", "collect"}},
    {"key": "extract", "num": "03", "label": "Extract Findings", "event_stages": {"extract"}},
    {"key": "compare", "num": "04", "label": "Compare Evidence", "event_stages": {"compare", "contradictions"}},
    {"key": "synthesize", "num": "05", "label": "Synthesize", "event_stages": {"synthesize", "done"}},
]


def render_stepper(events: list[dict], status: str):
    seen_stages = {e["stage"] for e in events}
    stage_counts = {}
    for e in events:
        stage_counts.setdefault(e["stage"], 0)
        stage_counts[e["stage"]] += 1

    reached_idx = -1
    for i, s in enumerate(PIPELINE_STAGES):
        if s["event_stages"] & seen_stages:
            reached_idx = i

    steps_html = []
    for i, s in enumerate(PIPELINE_STAGES):
        touched = bool(s["event_stages"] & seen_stages)
        is_last_reached = (i == reached_idx) and status == "running"
        if status == "done" and touched:
            css_class = "done"
        elif status == "failed" and touched and i == reached_idx:
            css_class = "active"
        elif is_last_reached:
            css_class = "active"
        elif touched:
            css_class = "done"
        else:
            css_class = ""

        sub_count = sum(stage_counts.get(es, 0) for es in s["event_stages"])
        sub_text = f"{sub_count} event(s)" if sub_count else ""

        steps_html.append(
            f'<div class="step {css_class}">'
            f'<div class="step-circle">{s["num"]}</div>'
            f'<div class="step-label">{s["label"]}</div>'
            f'<div class="step-sub">{sub_text}</div>'
            f'</div>'
        )

    n = len(PIPELINE_STAGES)
    progress_ratio = max(reached_idx, 0) / (n - 1) if reached_idx >= 0 else 0.0
    if status == "done":
        progress_ratio = 1.0
    progress_pct = round(progress_ratio * 86, 1)

    html = f"""
    <div class="stepper-wrap">
        <div class="stepper-line-base"></div>
        <div class="stepper-line-progress" style="width:{progress_pct}%;"></div>
        <div class="stepper">{''.join(steps_html)}</div>
    </div>
    """
    st.markdown(html, unsafe_allow_html=True)


def render_metric_row(stats: dict):
    items = [
        ("Sub-questions", stats["sub_question_count"]),
        ("Sources", stats["source_count"]),
        ("Findings", stats["finding_count"]),
        ("Corroborated", stats["corroborated_count"]),
        ("Contested", stats["contested_count"]),
        ("Contradictions", stats["contradiction_count"]),
        ("Conclusions", stats["conclusion_count"]),
    ]
    cards = "".join(
        f'<div class="metric-card"><div class="metric-value">{v}</div><div class="metric-label">{label}</div></div>'
        for label, v in items
    )
    st.markdown(f'<div class="metric-row">{cards}</div>', unsafe_allow_html=True)


def render_classification_chart(stats: dict):
    labels = ["Corroborated", "Single source", "Contested"]
    values = [stats["corroborated_count"], stats["single_source_count"], stats["contested_count"]]
    colors = ["#2F6E4F", "#8A6B2A", "#A13D3D"]
    if sum(values) == 0:
        return
    fig = go.Figure(go.Bar(
        x=values, y=labels, orientation="h",
        marker_color=colors,
        text=values, textposition="outside",
    ))
    fig.update_layout(
        height=180,
        margin=dict(l=10, r=10, t=10, b=10),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="IBM Plex Mono, monospace", size=12, color="#14181F"),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


def _confidence(findings: list[dict]):
    if not findings:
        return "Unverified", "single_source"
    corroborated = sum(1 for f in findings if f["classification"] == "corroborated")
    contested = sum(1 for f in findings if f["classification"] == "contested")
    if contested > 0 and contested >= corroborated:
        return "Disputed", "contested"
    if corroborated / len(findings) >= 0.5:
        return "Strong evidence", "corroborated"
    return "Limited evidence", "single_source"


def render_conclusion_card(index: int, conclusion: dict):
    label, css_class = _confidence(conclusion["findings"])
    with st.container(border=True):
        st.markdown(
            f'<span class="concl-index">FINDING {index:02d}</span> '
            f'<span class="badge badge-{css_class}">{label}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="concl-text">{conclusion["text"]}</div>', unsafe_allow_html=True)
        df = pd.DataFrame([
            {"Claim": f["claim"], "Classification": f["classification"].replace("_", " "), "Source": f["source_url"]}
            for f in conclusion["findings"]
        ])
        st.dataframe(
            df, use_container_width=True, hide_index=True,
            column_config={"Source": st.column_config.LinkColumn("Source")},
        )


def render_contradiction_card(contradiction: dict):
    with st.container(border=True):
        st.markdown(
            f'<span class="badge badge-contested">Contradiction</span>&nbsp;&nbsp;{contradiction["explanation"] or ""}',
            unsafe_allow_html=True,
        )
        col_a, col_b = st.columns(2)
        with col_a:
            st.caption("Source A")
            st.write(contradiction["finding_a"]["claim"])
            st.markdown(f'[{contradiction["finding_a"]["source_url"]}]({contradiction["finding_a"]["source_url"]})')
        with col_b:
            st.caption("Source B")
            st.write(contradiction["finding_b"]["claim"])
            st.markdown(f'[{contradiction["finding_b"]["source_url"]}]({contradiction["finding_b"]["source_url"]})')


# --------------------------------------------------------------------------- app
inject_base_styles()

st.markdown(
    """
    <div class="app-header">
        <div class="app-title">Enterprise AI Research Agent</div>
        <div class="app-subtitle">MULTI-AGENT RESEARCH PIPELINE &middot; STRUCTURED EVIDENCE &middot; FULL TRACEABILITY</div>
    </div>
    """,
    unsafe_allow_html=True,
)

tab_new, tab_kb, tab_about = st.tabs(["New Research", "Knowledge Base", "Architecture"])


# ---------------------------------------------------------------- New Research
with tab_new:
    st.write(
        "Submit any research question, in any industry. A classifier agent detects the domain "
        "and plans the research; downstream agents search, extract, cross-check, and synthesize "
        "evidence-backed conclusions."
    )
    question = st.text_input(
        "Research question",
        placeholder="e.g. How is AI transforming retail operations?",
        label_visibility="collapsed",
    )
    submit = st.button("Run research", type="primary")

    if submit and question.strip():
        resp = api_post("/research", json={"question": question.strip()})
        st.session_state["active_topic_id"] = resp["id"]

    topic_id = st.session_state.get("active_topic_id")
    if topic_id:
        header_box = st.empty()
        stepper_box = st.empty()
        log_box = st.empty()
        results_box = st.empty()

        for _ in range(180):  # ~6 minute max poll window
            detail = api_get(f"/research/{topic_id}")

            with header_box.container():
                domain = detail.get("domain")
                domain_html = f'<span class="badge badge-domain">{domain}</span>' if domain else ""
                st.markdown(
                    f'<div style="margin-bottom:4px;"><strong>Status:</strong> {detail["status"]} &nbsp;&nbsp; '
                    f'<strong>Domain:</strong> {domain_html or "detecting&hellip;"}</div>',
                    unsafe_allow_html=True,
                )

            with stepper_box.container():
                render_stepper(detail["events"], detail["status"])

            with log_box.container():
                with st.expander("Activity log", expanded=False):
                    for e in detail["events"]:
                        st.markdown(
                            f'<span style="font-family:\'IBM Plex Mono\',monospace;font-size:0.78rem;color:var(--muted);">'
                            f'[{e["stage"]}]</span> {e["message"]}',
                            unsafe_allow_html=True,
                        )

            if detail["status"] in ("done", "failed"):
                with results_box.container():
                    if detail["status"] == "done":
                        render_metric_row(detail["stats"])

                        col_chart, col_gap = st.columns([2, 1])
                        with col_chart:
                            st.markdown("**Evidence classification**")
                            render_classification_chart(detail["stats"])

                        st.markdown("### Conclusions")
                        for i, c in enumerate(detail["conclusions"], start=1):
                            render_conclusion_card(i, c)

                        if detail["contradictions"]:
                            st.markdown("### Contradictions detected")
                            for c in detail["contradictions"]:
                                render_contradiction_card(c)

                        st.markdown("### All findings")
                        st.caption("Every finding extracted during this run, grouped by sub-question.")
                        for group in detail["findings_by_sub_question"]:
                            with st.expander(f"{group['sub_question']}  ({len(group['findings'])} findings)"):
                                if group["findings"]:
                                    df = pd.DataFrame([
                                        {
                                            "Claim": f["claim"], "Detail": f["detail"] or "",
                                            "Classification": f["classification"].replace("_", " "),
                                            "Source": f["source_url"],
                                        }
                                        for f in group["findings"]
                                    ])
                                    st.dataframe(
                                        df, use_container_width=True, hide_index=True,
                                        column_config={"Source": st.column_config.LinkColumn("Source")},
                                    )
                                    st.download_button(
                                        "Download as CSV", df.to_csv(index=False),
                                        file_name=f"findings_{topic_id}.csv",
                                        key=f"dl_{group['sub_question'][:20]}_{topic_id}",
                                    )
                                else:
                                    st.caption("No findings extracted for this sub-question.")
                    else:
                        st.error("Pipeline failed before producing results. See the activity log above for details.")
                break

            time.sleep(2)


# ------------------------------------------------------------------- Knowledge Base
with tab_kb:
    st.markdown("### Past research runs")
    topics = api_get("/research")
    if not topics:
        st.caption("No research runs yet. Submit one in the New Research tab.")
    for t in topics:
        domain_html = f'<span class="badge badge-domain">{t.get("domain")}</span>' if t.get("domain") else ""
        with st.expander(f"{t['question']}  —  {t['status']}"):
            st.markdown(domain_html, unsafe_allow_html=True)
            detail = api_get(f"/research/{t['id']}")
            if detail["status"] == "done":
                render_metric_row(detail["stats"])
                for c in detail["conclusions"]:
                    st.markdown(f"- {c['text']}")

    st.divider()
    st.markdown("### Search the knowledge base")
    st.caption("Semantic search across every finding ever extracted, from any past research run.")
    kb_query = st.text_input("Search", key="kb_search", label_visibility="collapsed", placeholder="e.g. demand forecasting")
    if kb_query:
        results = api_get("/knowledge-base/search", params={"q": kb_query})
        if results["results"]:
            df = pd.DataFrame([
                {"Finding": h["text"], "Domain": h["metadata"].get("domain", ""), "Source": h["metadata"].get("source_url", "")}
                for h in results["results"]
            ])
            st.dataframe(
                df, use_container_width=True, hide_index=True,
                column_config={"Source": st.column_config.LinkColumn("Source")},
            )
        else:
            st.caption("No matching findings yet.")


# ------------------------------------------------------------------------- Architecture
with tab_about:
    st.markdown("### Pipeline")
    render_stepper(
        [{"stage": s, "message": ""} for stage in PIPELINE_STAGES for s in stage["event_stages"]],
        status="done",
    )
    st.markdown(
        """
| Layer | Component | Notes |
|---|---|---|
| UI | Streamlit (`frontend/app.py`) | This dashboard |
| API | FastAPI (`backend/main.py`, `backend/routes/`) | `/research` endpoints |
| AI Intelligence | 5-agent pipeline (`backend/agents/`) | Classifier &rarr; Search &rarr; Extraction &rarr; Evidence &rarr; Synthesis |
| Data & Knowledge | SQLite + ChromaDB (`backend/db/`) | Persistent, restart-safe, offline vector search |
| External research | Tavily search API | Free tier, agent-oriented |
| LLM | Groq (Llama 3.3 70B) | Free tier, open-weight model |
"""
    )
    st.caption("Full detail, including design rationale, in README.md and docs/architecture.md in the repository.")
