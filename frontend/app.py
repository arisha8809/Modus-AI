"""The Brief — focused intelligence-console demo UI."""
from __future__ import annotations

import os
import time
from html import escape

import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()
BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000").rstrip("/")
st.set_page_config(page_title="The Brief", page_icon="◒", layout="wide", initial_sidebar_state="collapsed")


def get(path: str):
    try:
        response = requests.get(f"{BACKEND_URL}{path}", timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException:
        return None


def post(path: str, payload: dict):
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=12)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        st.error(f"Unable to start the brief: {exc}")
        return None


def styles():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=Manrope:wght@400;500;600;700;800&display=swap');
    :root{--bg:#0b0d12;--panel:#11141b;--line:#252b36;--text:#e8eaf0;--muted:#818896;--lime:#c9f27a;--violet:#9c8cff;--red:#ff7e86}
    html,body,[class*="css"]{font-family:Manrope,system-ui,sans-serif;color:var(--text)}
    .stApp{background:radial-gradient(ellipse at 78% -10%,#24204d 0,transparent 38rem),radial-gradient(ellipse at -10% 75%,#132820 0,transparent 32rem),var(--bg)}
    [data-testid="stHeader"]{background:transparent}.block-container{max-width:1260px;padding:1.25rem 3.5rem 5rem}
    .top{display:flex;justify-content:space-between;align-items:center;padding:.5rem 0 3rem;border-bottom:1px solid var(--line)}
    .identity{display:flex;align-items:center;gap:.8rem}.symbol{width:36px;height:36px;display:grid;place-items:center;border:1px solid #ffffff2e;border-radius:50%;color:var(--lime);font-size:1.1rem}.wordmark{font-size:.88rem;font-weight:800;letter-spacing:.16em;text-transform:uppercase}.descriptor{font-family:'DM Mono',monospace;color:var(--muted);font-size:.65rem;margin-top:.2rem}.system{display:flex;align-items:center;gap:.55rem;color:var(--muted);font-family:'DM Mono',monospace;font-size:.68rem;text-transform:uppercase;letter-spacing:.08em}.pulse{width:7px;height:7px;border-radius:50%;background:var(--lime);box-shadow:0 0 0 5px #c9f27a14}
    .hero{padding:5.1rem 0 4.4rem;max-width:920px}.kicker{color:var(--lime);font-family:'DM Mono',monospace;font-size:.7rem;letter-spacing:.13em;text-transform:uppercase}.hero h1{color:var(--text)!important;font-size:clamp(2.8rem,7vw,6.2rem);line-height:.98;letter-spacing:-.075em;margin:1.25rem 0 1.4rem;font-weight:800}.hero h1 em{color:var(--violet);font-style:normal}.hero-copy{max-width:610px;color:#aeb3bd;font-size:1.05rem;line-height:1.75}.hero-rule{width:80px;height:2px;background:var(--lime);margin-top:2.5rem}
    .workspace{display:grid;grid-template-columns:1fr 300px;gap:5rem;align-items:start}.eyebrow{font-family:'DM Mono',monospace;color:var(--muted);font-size:.66rem;letter-spacing:.12em;text-transform:uppercase}.section-title{font-size:1.35rem;letter-spacing:-.04em;margin:.65rem 0 .45rem}.section-copy{color:var(--muted);font-size:.85rem;line-height:1.6;max-width:600px;margin:0 0 1.5rem}
    .form-shell{border-top:1px solid var(--line);border-bottom:1px solid var(--line);padding:1.5rem 0 1.8rem}.field-label{display:block;color:#aeb3bd;font-family:'DM Mono',monospace;font-size:.68rem;letter-spacing:.08em;text-transform:uppercase;margin-bottom:.65rem}.stTextArea textarea{background:#0d1016!important;color:var(--text)!important;border:1px solid var(--line)!important;border-radius:3px!important;font-size:1rem!important;line-height:1.65!important;padding:1rem!important}.stTextArea textarea:focus{border-color:var(--violet)!important;box-shadow:0 0 0 1px var(--violet)!important}.stSelectbox>div>div{background:#0d1016!important;border:1px solid var(--line)!important;border-radius:3px!important;color:var(--text)!important}.stButton>button{border:1px solid var(--lime)!important;border-radius:2px!important;background:var(--lime)!important;color:#10140d!important;font-weight:800!important;letter-spacing:.02em!important;min-height:46px!important}.stButton>button:hover{background:#e0ffa1!important;border-color:#e0ffa1!important;transform:translateY(-1px)}
    .side{border-left:1px solid var(--line);padding-left:2rem}.side-title{font-size:.78rem;font-weight:700;color:#d9dce3;margin:.8rem 0 1.4rem}.signal{padding:.9rem 0;border-bottom:1px solid var(--line)}.signal:last-child{border-bottom:0}.signal-no{font-family:'DM Mono',monospace;color:var(--violet);font-size:.65rem}.signal strong{display:block;color:var(--text);font-size:.78rem;margin:.35rem 0}.signal p{color:var(--muted);font-size:.72rem;line-height:1.5;margin:0}
    .runbar{display:flex;align-items:center;justify-content:space-between;gap:1rem;padding:1rem 0;border-bottom:1px solid var(--line);font-family:'DM Mono',monospace;font-size:.68rem;color:var(--muted)}.runbar strong{color:var(--lime);font-weight:500}.stage-row{display:flex;gap:0;margin:1.8rem 0 2.5rem}.stage{flex:1;border-top:2px solid var(--line);padding-top:.75rem;margin-right:1rem}.stage.on{border-color:var(--lime)}.stage-no{font-family:'DM Mono',monospace;color:var(--muted);font-size:.64rem}.stage.on .stage-no{color:var(--lime)}.stage-name{font-size:.75rem;color:#c7cbd3;margin-top:.35rem}.result-grid{display:grid;grid-template-columns:1.5fr 1fr;gap:3rem}.result-label{font-family:'DM Mono',monospace;color:var(--violet);font-size:.65rem;text-transform:uppercase;letter-spacing:.1em}.result-heading{font-size:1.7rem;letter-spacing:-.05em;line-height:1.2;margin:.65rem 0 1rem}.result-copy{color:#aeb3bd;line-height:1.7;font-size:.86rem}.finding{border-top:1px solid var(--line);padding:1rem 0}.finding b{display:block;font-size:.82rem;line-height:1.5;margin-bottom:.3rem}.finding span{color:var(--muted);font-size:.72rem;line-height:1.5}.finding a{color:var(--lime);text-decoration:none}.metricline{display:flex;justify-content:space-between;border-bottom:1px solid var(--line);padding:.8rem 0;color:var(--muted);font-size:.75rem}.metricline strong{color:var(--text);font-family:'DM Mono',monospace;font-weight:500}.back{color:var(--muted);font-family:'DM Mono',monospace;font-size:.68rem;cursor:pointer}.empty{color:var(--muted);font-family:'DM Mono',monospace;font-size:.72rem;padding:2rem 0}
    @media(max-width:850px){.block-container{padding:1rem 1.25rem 3rem}.top{padding-bottom:2rem}.system{display:none}.hero{padding:3.5rem 0 3rem}.hero h1{font-size:3.2rem}.workspace,.result-grid{grid-template-columns:1fr;gap:2.5rem}.side{border-left:0;border-top:1px solid var(--line);padding:1.5rem 0 0}.stage-row{overflow-x:auto}.stage{min-width:110px}}
    </style>
    """, unsafe_allow_html=True)


def header():
    st.markdown('<div class="top"><div class="identity"><div class="symbol">◒</div><div><div class="wordmark">The Brief</div><div class="descriptor">intelligence / 01</div></div></div><div class="system"><span class="pulse"></span> engine online · local workspace</div></div>', unsafe_allow_html=True)


def new_brief():
    st.markdown('<div class="hero"><div class="kicker">Evidence-grounded decision support</div><h1>Make the signal<br><em>impossible to miss.</em></h1><p class="hero-copy">The Brief turns a complex business question into a clear, source-backed decision. It finds the signal, tests the evidence, and shows you exactly what deserves attention.</p><div class="hero-rule"></div></div>', unsafe_allow_html=True)
    st.markdown('<div class="workspace"><main><div class="eyebrow">01 / Start an intelligence run</div><div class="section-title">What decision are you trying to make?</div><p class="section-copy">Give the engine a question with stakes. The result is not a chat response — it is a structured brief with evidence, uncertainty, and a next move.</p><div class="form-shell">', unsafe_allow_html=True)
    with st.form("brief_form"):
        question = st.text_area("Business question", value="Which operational risks should leadership review before approving the next expansion phase?", height=130, label_visibility="visible")
        a, b = st.columns(2)
        with a:
            st.selectbox("Intelligence mode", ["Operational risk review", "Executive decision brief", "Market intelligence", "Exception investigation"])
        with b:
            st.selectbox("Decision audience", ["Leadership team", "Operations", "Product and engineering", "Risk and compliance"])
        submitted = st.form_submit_button("Run the brief  →", use_container_width=True)
    st.markdown('</div></main><aside class="side"><div class="eyebrow">What happens next</div><div class="side-title">A controlled path from question to action.</div><div class="signal"><span class="signal-no">01</span><strong>Find the signal</strong><p>Break the question into focused research threads.</p></div><div class="signal"><span class="signal-no">02</span><strong>Test the evidence</strong><p>Compare sources, surface gaps, and expose contradictions.</p></div><div class="signal"><span class="signal-no">03</span><strong>Make it accountable</strong><p>Trace every important conclusion back to its source.</p></div></aside></div>', unsafe_allow_html=True)
    if submitted:
        if not question.strip():
            st.warning("Add a business question first.")
            return
        result = post("/research", {"question": question.strip()})
        if result:
            st.session_state.topic_id = result.get("id")
            time.sleep(.35)
            st.rerun()


def result_view(detail: dict):
    if st.button("← New brief", key="new_brief", help="Return to a clean starting screen"):
        st.session_state.pop("topic_id", None)
        st.rerun()
    st.markdown(f'<div class="runbar"><span>RUN / {detail.get("id", "--")}</span><strong>● {escape(detail.get("status", "processing").upper())}</strong><span>Evidence graph assembled</span></div>', unsafe_allow_html=True)
    stages = [("01", "Discover"), ("02", "Collect"), ("03", "Understand"), ("04", "Validate"), ("05", "Recommend")]
    st.markdown('<div class="stage-row">' + ''.join(f'<div class="stage on"><div class="stage-no">{n}</div><div class="stage-name">{name}</div></div>' for n,name in stages) + '</div>', unsafe_allow_html=True)
    stats = detail.get("stats", {})
    analytics = detail.get("analytics", {})
    conclusions = detail.get("conclusions", [])
    findings = [f for group in detail.get("findings_by_sub_question", []) for f in group.get("findings", [])]
    st.markdown(f'<div class="result-grid"><section><div class="result-label">Executive readout</div><div class="result-heading">{escape(detail.get("question", "Untitled brief"))}</div><p class="result-copy">The system has assembled an evidence-backed view of this decision. Review the recommendations below, then follow the source trail before acting.</p>', unsafe_allow_html=True)
    if conclusions:
        for item in conclusions[:4]:
            st.markdown(f'<div class="finding"><b>{escape(item.get("text", ""))}</b><span>{len(item.get("findings", []))} supporting finding(s) · source-backed</span></div>', unsafe_allow_html=True)
    elif findings:
        st.markdown('<div class="empty">The reasoning layer is still assembling the executive readout. Refresh shortly.</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty">No findings returned yet. The pipeline may still be running.</div>', unsafe_allow_html=True)
    st.markdown('</section><aside class="side"><div class="result-label">System readout</div><div class="metricline"><span>Sources analyzed</span><strong>' + str(stats.get("source_count", 0)) + '</strong></div><div class="metricline"><span>Evidence signals</span><strong>' + str(stats.get("finding_count", 0)) + '</strong></div><div class="metricline"><span>Corroborated</span><strong>' + str(stats.get("corroborated_count", 0)) + '</strong></div><div class="metricline"><span>Needs review</span><strong>' + str(stats.get("contradiction_count", 0)) + '</strong></div><div class="metricline"><span>Date coverage</span><strong>' + str(analytics.get("date_coverage_percent", 0)) + '%</strong></div></aside></div>', unsafe_allow_html=True)
    if findings:
        st.markdown('<div style="margin-top:4rem" class="eyebrow">Evidence layer / source trail</div><div class="section-title">What the system found</div>', unsafe_allow_html=True)
        for finding in findings[:8]:
            source = escape(finding.get("source_url", "#"))
            st.markdown(f'<div class="finding"><b>{escape(finding.get("claim", ""))}</b><span>{escape(finding.get("detail") or "Source-backed finding")} · <a href="{source}" target="_blank">open source ↗</a></span></div>', unsafe_allow_html=True)


def main():
    styles()
    header()
    topic_id = st.session_state.get("topic_id")
    if topic_id:
        detail = get(f"/research/{topic_id}")
        if detail:
            result_view(detail)
            return
        st.session_state.pop("topic_id", None)
    new_brief()


main()
