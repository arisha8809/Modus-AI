"""The Brief — evidence-grounded enterprise intelligence workspace."""
from __future__ import annotations

import os
import time
from html import escape

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")

st.set_page_config(page_title="The Brief · Intelligence Workspace", page_icon="◈", layout="wide", initial_sidebar_state="collapsed")


def api_get(path: str, params: dict | None = None, quiet: bool = False):
    try:
        response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        if not quiet:
            st.error(f"The intelligence API is unavailable: {exc}")
        return None


def api_post(path: str, payload: dict):
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"The intelligence API could not start this brief: {exc}")
        return None


def inject_styles():
    st.markdown("""
    <style>
    :root{--ink:#172033;--muted:#667085;--line:#e7eaf0;--paper:#f6f7fb;--blue:#3157d5;--blue-soft:#eef2ff;--green:#16845b;--green-soft:#eaf8f1;--amber:#aa6d09;--amber-soft:#fff7e6}
    html,body,[class*="css"]{font-family:Inter,ui-sans-serif,system-ui,-apple-system,"Segoe UI",sans-serif;color:var(--ink)}
    .stApp{background:radial-gradient(circle at 95% 0%,#edf1ff 0,transparent 25rem),var(--paper)}
    [data-testid="stHeader"]{background:transparent}.block-container{max-width:1420px;padding:2rem 3rem 4rem}
    .topbar{display:flex;align-items:center;justify-content:space-between;margin-bottom:1.4rem}.brand{display:flex;gap:.75rem;align-items:center}.brand-mark{display:grid;place-items:center;width:40px;height:40px;border-radius:12px;color:#fff;background:linear-gradient(135deg,#2445b8,#6d54dc);font-weight:800;box-shadow:0 8px 18px #3157d533}.brand-name{font-weight:800;letter-spacing:-.02em}.brand-sub{color:var(--muted);font-size:.74rem;margin-top:2px}.live{display:inline-flex;align-items:center;gap:.45rem;border:1px solid #cdebdc;border-radius:999px;background:#f3fcf7;color:var(--green);font-size:.72rem;font-weight:750;padding:.4rem .7rem;text-transform:uppercase;letter-spacing:.08em}.live-dot{width:7px;height:7px;border-radius:50%;background:#1db879;box-shadow:0 0 0 4px #1db87922}
    .hero{position:relative;overflow:hidden;padding:2.25rem 2.4rem;border-radius:22px;color:#fff;background:linear-gradient(125deg,#111b3a,#273f9c 62%,#5a4bb7);box-shadow:0 22px 55px #17255424}.hero:after{content:"";position:absolute;width:270px;height:270px;right:-70px;bottom:-145px;border:1px solid #ffffff2c;border-radius:50%;box-shadow:0 0 0 28px #ffffff08,0 0 0 58px #ffffff05}.hero-kicker{color:#cdd7ff;font-size:.72rem;font-weight:800;letter-spacing:.15em;text-transform:uppercase}.hero h1{position:relative;z-index:1;color:#fff!important;font-size:clamp(2rem,4vw,3.45rem);letter-spacing:-.06em;line-height:1.02;max-width:790px;margin:.65rem 0 .85rem}.hero p{position:relative;z-index:1;max-width:680px;color:#dbe3ff;line-height:1.6;margin:0;font-size:1rem}.hero-pills{position:relative;z-index:1;display:flex;flex-wrap:wrap;gap:.5rem;margin-top:1.3rem}.hero-pill{padding:.4rem .65rem;border:1px solid #cdd7ff3b;border-radius:7px;background:#ffffff12;color:#e7ebff;font-size:.74rem}
    .section-head{display:flex;align-items:end;justify-content:space-between;gap:1rem;margin:2rem 0 .8rem}.eyebrow{color:var(--blue);font-size:.7rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.section-title{font-size:1.45rem;font-weight:800;letter-spacing:-.04em;margin:.2rem 0 0}.section-note{color:var(--muted);font-size:.86rem;line-height:1.5;margin:.35rem 0 0}.panel{background:#ffffffd9;border:1px solid var(--line);border-radius:16px;padding:1.15rem 1.25rem;box-shadow:0 12px 30px #1b25400a}.panel-title{font-size:.96rem;font-weight:800;margin-bottom:.25rem}.panel-copy{color:var(--muted);font-size:.8rem;line-height:1.5;margin:0}.metric{background:#fff;border:1px solid var(--line);border-radius:14px;padding:1rem;min-height:92px}.metric-label{color:var(--muted);font-size:.72rem;font-weight:700;text-transform:uppercase;letter-spacing:.06em}.metric-value{color:var(--ink);font-size:1.65rem;font-weight:820;letter-spacing:-.04em;margin-top:.25rem}.metric-foot{color:var(--green);font-size:.72rem;margin-top:.1rem}.stage{display:flex;align-items:center;gap:.75rem;padding:.65rem 0;border-bottom:1px solid #eef0f4}.stage:last-child{border-bottom:0}.stage-num{display:grid;place-items:center;width:26px;height:26px;border-radius:8px;background:var(--blue-soft);color:var(--blue);font-size:.7rem;font-weight:800}.stage-name{font-size:.81rem;font-weight:700;flex:1}.stage-state{color:var(--muted);font-size:.7rem}.stage-state.done{color:var(--green);font-weight:750}.stage-state.running{color:var(--amber);font-weight:750}.signal{padding:.85rem .95rem;border:1px solid var(--line);border-radius:11px;background:#fff;margin:.55rem 0}.signal-label{color:var(--muted);font-size:.7rem;font-weight:750;text-transform:uppercase;letter-spacing:.06em}.signal-text{font-size:.82rem;line-height:1.45;margin-top:.22rem}.finding{padding:1rem 0;border-bottom:1px solid #edf0f4}.finding:last-child{border-bottom:0}.tag{display:inline-block;border-radius:999px;padding:.22rem .48rem;font-size:.66rem;font-weight:800;text-transform:uppercase;letter-spacing:.05em}.tag-green{color:var(--green);background:var(--green-soft)}.tag-amber{color:var(--amber);background:var(--amber-soft)}.tag-blue{color:var(--blue);background:var(--blue-soft)}.finding-title{font-size:.9rem;font-weight:760;margin:.42rem 0 .25rem;line-height:1.4}.finding-detail{color:var(--muted);font-size:.78rem;line-height:1.5}.source{display:flex;justify-content:space-between;gap:.6rem;padding:.7rem 0;border-bottom:1px solid #edf0f4;font-size:.77rem}.source a{color:var(--blue);text-decoration:none;overflow-wrap:anywhere}.source small{color:var(--muted);white-space:nowrap}.empty{padding:2rem;text-align:center;color:var(--muted);border:1px dashed #cfd5e2;border-radius:14px;background:#ffffff99}div[data-testid="stButton"] button{border-radius:9px;font-weight:750}div[data-testid="stTextArea"] textarea,div[data-testid="stTextInput"] input{border-radius:10px;border-color:#d9deea}
    </style>
    """, unsafe_allow_html=True)


def card(title: str, copy: str = ""):
    st.markdown(f'<div class="panel"><div class="panel-title">{escape(title)}</div><p class="panel-copy">{escape(copy)}</p>', unsafe_allow_html=True)


def close_card():
    st.markdown("</div>", unsafe_allow_html=True)


def status_tag(value: str) -> str:
    value = (value or "unknown").replace("_", " ")
    color = "green" if value in {"corroborated", "completed", "complete", "ready"} else "amber" if value in {"contested", "running", "pending"} else "blue"
    return f'<span class="tag tag-{color}">{escape(value)}</span>'


def render_topbar():
    st.markdown('<div class="topbar"><div class="brand"><div class="brand-mark">◈</div><div><div class="brand-name">The Brief</div><div class="brand-sub">Enterprise intelligence workspace</div></div></div><div class="live"><span class="live-dot"></span> Intelligence engine online</div></div>', unsafe_allow_html=True)


def render_hero():
    st.markdown('<div class="hero"><div class="hero-kicker">Evidence-grounded decision support</div><h1>Turn fragmented information into a decision you can defend.</h1><p>The Brief orchestrates research, evidence, and reasoning into clear operational intelligence — with every important conclusion traceable to its source.</p><div class="hero-pills"><span class="hero-pill">Traceable evidence</span><span class="hero-pill">Multi-stage reasoning</span><span class="hero-pill">Production-ready workflow</span></div></div>', unsafe_allow_html=True)


def render_metrics(topics: list[dict], selected: dict | None):
    stats = selected.get("stats", {}) if selected else {}
    values = [("Active briefs", str(len(topics)), "Workspace history"), ("Sources analyzed", str(stats.get("source_count", "—")), "Selected brief"), ("Evidence-backed findings", str(stats.get("finding_count", "—")), "Traceable signals"), ("Review items", str(stats.get("contradiction_count", "—")), "Needs attention")]
    cols = st.columns(4)
    for col, (label, value, foot) in zip(cols, values):
        with col:
            st.markdown(f'<div class="metric"><div class="metric-label">{escape(label)}</div><div class="metric-value">{escape(value)}</div><div class="metric-foot">{escape(foot)}</div></div>', unsafe_allow_html=True)


def render_stage_panel(selected: dict | None):
    card("Intelligence pipeline", "A visible chain from question to accountable recommendation.")
    stages = [("01", "Discover", "done"), ("02", "Collect", "done"), ("03", "Understand", "done"), ("04", "Validate", "done"), ("05", "Recommend", "done")]
    if selected and selected.get("status") not in {"completed", "complete"}:
        stages[-1] = ("05", "Recommend", "running")
    for number, name, state in stages:
        label = "Complete" if state == "done" else "In progress"
        st.markdown(f'<div class="stage"><div class="stage-num">{number}</div><div class="stage-name">{name}</div><div class="stage-state {state}">{label}</div></div>', unsafe_allow_html=True)
    close_card()


def render_brief_list(topics: list[dict]):
    card("Recent briefs", "Each brief becomes a reusable, searchable evidence record.")
    if not topics:
        st.markdown('<div class="empty">No briefs yet. Start with the prepared operational-risk scenario.</div>', unsafe_allow_html=True)
    else:
        for topic in topics[:6]:
            title = topic.get("question", "Untitled brief")
            if st.button(title[:74], key=f"topic_{topic['id']}", use_container_width=True):
                st.session_state.selected_topic_id = topic["id"]
                st.rerun()
            st.caption(f"{status_tag(topic.get('status', 'ready'))}  ·  {str(topic.get('created_at', ''))[:16]}", unsafe_allow_html=True)
    close_card()


def render_create_form():
    st.markdown('<div class="section-head"><div><div class="eyebrow">Create intelligence</div><div class="section-title">Start a new brief</div><p class="section-note">Describe the decision or operational question. The engine will break it into researchable threads and preserve the evidence behind each result.</p></div></div>', unsafe_allow_html=True)
    with st.form("create_brief", clear_on_submit=False):
        col1, col2 = st.columns([1.5, 1])
        with col1:
            question = st.text_area("Business question", value="Which operational risks should leadership review before approving the next expansion phase?", height=115)
        with col2:
            brief_type = st.selectbox("Brief type", ["Operational risk review", "Executive decision brief", "Market intelligence", "Exception investigation"])
            audience = st.selectbox("Audience", ["Leadership team", "Operations", "Product and engineering", "Risk and compliance"])
        submitted = st.form_submit_button("Run intelligence brief", type="primary", use_container_width=True)
    if submitted:
        if not question.strip():
            st.warning("Add a business question first.")
        else:
            result = api_post("/research", {"question": question.strip()})
            if result:
                st.session_state.selected_topic_id = result.get("id")
                st.success(f"{brief_type} started for {audience.lower()}.")
                time.sleep(.4)
                st.rerun()


def render_detail(detail: dict):
    stats = detail.get("stats", {})
    analytics = detail.get("analytics", {})
    st.markdown(f'<div class="section-head"><div><div class="eyebrow">Brief result · {escape(detail.get("domain") or "Enterprise intelligence")}</div><div class="section-title">{escape(detail.get("question", "Untitled brief"))}</div><p class="section-note">Status {status_tag(detail.get("status", "ready"))} · Every conclusion below can be traced to its supporting findings and source records.</p></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    left, right = st.columns([1.65, 1])
    with left:
        st.markdown('<div class="panel-title">Executive readout</div><p class="panel-copy">A decision-oriented view of what the evidence says, where it is strong, and what deserves human review.</p>', unsafe_allow_html=True)
        conclusions = detail.get("conclusions", [])
        if conclusions:
            for conclusion in conclusions[:4]:
                st.markdown(f'<div class="finding"><span class="tag tag-blue">Recommendation</span><div class="finding-title">{escape(conclusion.get("text", ""))}</div><div class="finding-detail">{len(conclusion.get("findings", []))} supporting finding(s) · source-backed</div></div>', unsafe_allow_html=True)
        else:
            st.info("The pipeline is still assembling the executive readout. Refresh in a moment.")
    with right:
        st.markdown('<div class="panel-title">Decision signals</div>', unsafe_allow_html=True)
        signals = analytics.get("decision_signals", {})
        for label, key in [("Strongest evidence", "strongest_evidence"), ("Needs review", "needs_review"), ("Coverage gaps", "coverage_gaps")]:
            items = signals.get(key, [])
            text = items[0] if items else "No signal recorded"
            st.markdown(f'<div class="signal"><div class="signal-label">{escape(label)}</div><div class="signal-text">{escape(text)}</div></div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-head"><div><div class="eyebrow">Evidence layer</div><div class="section-title">Findings and source trail</div></div></div>', unsafe_allow_html=True)
    findings = [finding for group in detail.get("findings_by_sub_question", []) for finding in group.get("findings", [])]
    col1, col2 = st.columns([1.35, 1])
    with col1:
        card("Key findings", "Claims are stored separately from conclusions so reviewers can inspect the reasoning chain.")
        if not findings:
            st.markdown('<div class="empty">No findings are available yet.</div>', unsafe_allow_html=True)
        for finding in findings[:10]:
            source = finding.get("source_url", "#")
            st.markdown(f'<div class="finding">{status_tag(finding.get("classification", "single_source"))}<div class="finding-title">{escape(finding.get("claim", ""))}</div><div class="finding-detail">{escape(finding.get("detail") or "Evidence captured from the linked source record.")}</div><div class="finding-detail" style="margin-top:.45rem"><a href="{escape(source)}" target="_blank">{escape(finding.get("source_title") or source)}</a></div></div>', unsafe_allow_html=True)
        close_card()
    with col2:
        card("Operational profile", "Signals that help a reviewer judge coverage and confidence.")
        for label, value in [("Sources", stats.get("source_count", 0)), ("Findings", stats.get("finding_count", 0)), ("Corroborated", stats.get("corroborated_count", 0)), ("Contradictions", stats.get("contradiction_count", 0)), ("Date coverage", f"{analytics.get('date_coverage_percent', 0)}%")]:
            st.markdown(f'<div class="stage"><div class="stage-name">{escape(label)}</div><div class="stage-state done">{escape(str(value))}</div></div>', unsafe_allow_html=True)
        close_card()
    contradictions = detail.get("contradictions", [])
    if contradictions:
        st.markdown('<div class="section-head"><div><div class="eyebrow">Human review</div><div class="section-title">Contradictions to resolve</div></div></div>', unsafe_allow_html=True)
        for item in contradictions[:4]:
            with st.expander(item.get("explanation") or "Conflicting evidence"):
                st.write(item.get("finding_a", {}).get("claim", ""))
                st.write(item.get("finding_b", {}).get("claim", ""))


def main():
    inject_styles()
    render_topbar()
    render_hero()
    topics = api_get("/research", quiet=True) or []
    selected_id = st.session_state.get("selected_topic_id")
    selected = api_get(f"/research/{selected_id}", quiet=True) if selected_id else None
    if selected is None and topics:
        selected = api_get(f"/research/{topics[0]['id']}", quiet=True)
        if selected:
            st.session_state.selected_topic_id = topics[0]["id"]
    st.markdown('<div class="section-head"><div><div class="eyebrow">Workspace overview</div><div class="section-title">A clear path from question to action</div><p class="section-note">The Brief makes AI reasoning inspectable: watch the pipeline, review the evidence, and decide what should happen next.</p></div></div>', unsafe_allow_html=True)
    render_metrics(topics, selected)
    left, right = st.columns([1.15, 1])
    with left:
        render_stage_panel(selected)
    with right:
        render_brief_list(topics)
    tabs = st.tabs(["Create brief", "Brief result", "System view"])
    with tabs[0]:
        render_create_form()
    with tabs[1]:
        render_detail(selected) if selected else st.markdown('<div class="empty">Start a brief to see the evidence-backed result workspace.</div>', unsafe_allow_html=True)
    with tabs[2]:
        st.markdown('<div class="section-head"><div><div class="eyebrow">Production posture</div><div class="section-title">Designed to move from prototype to platform</div><p class="section-note">The operational surface stays visible so the system can be debugged, measured, and deployed rather than treated as a black-box prompt.</p></div></div>', unsafe_allow_html=True)
        c1, c2, c3 = st.columns(3)
        for col, title, copy in [(c1, "API-first", "FastAPI endpoints, typed payloads, OpenAPI documentation, and persisted pipeline state."), (c2, "Evidence-first", "Structured findings, semantic retrieval, contradictions, and source-level traceability."), (c3, "Deployment-ready", "Containerized services, health checks, environment configuration, and a clean path to GCP.")]:
            with col:
                card(title, copy)
                close_card()
        health = api_get("/health", quiet=True)
        st.success(f"Backend health: {health.get('status', 'ok')} · version {health.get('version', '1.0.0')}") if health else st.warning("Backend health is not reachable. Start the API to activate the live workspace.")


main()
