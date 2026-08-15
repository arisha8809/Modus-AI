"""Modus AI — Enterprise Research Intelligence dashboard.

The UI is intentionally evidence-first rather than chat-first. It gives users a
clear research workspace, live pipeline visibility, structured findings, and
traceable conclusions backed by source URLs.
"""

import os
import time
from html import escape

import pandas as pd
import plotly.graph_objects as go
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(
    page_title="Modus AI · Research Intelligence",
    page_icon="AI",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# --------------------------------------------------------------------------- API

def api_get(path: str, params: dict | None = None, stop_on_error: bool = True):
    """GET wrapper with an optional non-blocking mode for secondary tabs."""
    try:
        response = requests.get(f"{BACKEND_URL}{path}", params=params, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        if stop_on_error:
            st.error(
                f"The research engine is unavailable at {BACKEND_URL}. "
                "Start the FastAPI service and try again."
            )
            st.stop()
        return None
    except requests.exceptions.RequestException as exc:
        if stop_on_error:
            st.error(f"The backend request failed: {exc}")
            st.stop()
        return None


def api_post(path: str, json: dict):
    """POST wrapper with a clear, user-facing failure state."""
    try:
        response = requests.post(f"{BACKEND_URL}{path}", json=json, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ConnectionError:
        st.error(
            f"The research engine is unavailable at {BACKEND_URL}. "
            "Start the FastAPI service and try again."
        )
        st.stop()
    except requests.exceptions.RequestException as exc:
        st.error(f"The backend request failed: {exc}")
        st.stop()


# --------------------------------------------------------------------------- visual system

def inject_base_styles():
    """Inject only CSS in this markdown block.

    Keeping CSS separate from other HTML prevents Streamlit's markdown renderer
    from displaying the stylesheet as visible page text.
    """
    st.markdown(
        """
        <style>
        :root {
            --ink: #0f172a;
            --ink-soft: #334155;
            --muted: #64748b;
            --line: #e2e8f0;
            --paper: #f6f8fc;
            --panel: #ffffff;
            --blue: #2563eb;
            --blue-dark: #1d4ed8;
            --blue-soft: #eff6ff;
            --violet: #7c3aed;
            --green: #15803d;
            --green-soft: #ecfdf3;
            --amber: #a16207;
            --amber-soft: #fffbeb;
            --red: #b91c1c;
            --red-soft: #fef2f2;
            --shadow: 0 14px 40px rgba(15, 23, 42, 0.07);
        }

        html, body, [class*="css"] {
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont,
                         "Segoe UI", sans-serif;
            color: var(--ink);
        }

        .stApp {
            background:
                radial-gradient(circle at 92% 0%, rgba(37, 99, 235, 0.08), transparent 26rem),
                linear-gradient(180deg, #fbfcff 0%, var(--paper) 48%, #f8fafc 100%);
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        [data-testid="stToolbar"] {
            right: 1rem;
        }

        .block-container {
            max-width: 1420px;
            padding-top: 2.6rem;
            padding-bottom: 4rem;
        }

        h1, h2, h3, h4 {
            color: var(--ink) !important;
            letter-spacing: -0.025em;
        }

        h2 { margin-top: 0.35rem !important; }
        h3 { margin-top: 1.35rem !important; }

        .topbar {
            display: flex;
            justify-content: space-between;
            align-items: center;
            gap: 1.5rem;
            margin-bottom: 1.2rem;
        }

        .brand-lockup {
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }

        .brand-mark {
            width: 42px;
            height: 42px;
            display: grid;
            place-items: center;
            border-radius: 13px;
            color: #ffffff;
            background: linear-gradient(135deg, #1d4ed8 0%, #7c3aed 100%);
            box-shadow: 0 8px 20px rgba(37, 99, 235, 0.23);
            font-weight: 800;
            font-size: 0.82rem;
            letter-spacing: -0.04em;
        }

        .brand-name {
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 750;
            letter-spacing: 0.03em;
        }

        .brand-subtitle {
            color: var(--muted);
            font-size: 0.72rem;
            margin-top: 1px;
        }

        .status-pill {
            display: inline-flex;
            align-items: center;
            gap: 0.45rem;
            padding: 0.42rem 0.75rem;
            border: 1px solid #dbeafe;
            border-radius: 999px;
            background: rgba(239, 246, 255, 0.85);
            color: #1d4ed8;
            font-size: 0.72rem;
            font-weight: 700;
            letter-spacing: 0.04em;
            text-transform: uppercase;
        }

        .status-dot {
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #22c55e;
            box-shadow: 0 0 0 4px rgba(34, 197, 94, 0.13);
        }

        .hero {
            position: relative;
            overflow: hidden;
            padding: 2.15rem 2.25rem;
            border-radius: 24px;
            color: #ffffff;
            background:
                radial-gradient(circle at 84% 12%, rgba(129, 140, 248, 0.45), transparent 21rem),
                radial-gradient(circle at 9% 110%, rgba(14, 165, 233, 0.28), transparent 20rem),
                linear-gradient(125deg, #0f172a 0%, #172554 58%, #312e81 100%);
            box-shadow: 0 24px 60px rgba(30, 41, 59, 0.22);
        }

        .hero::after {
            content: "";
            position: absolute;
            width: 260px;
            height: 260px;
            right: -80px;
            bottom: -125px;
            border: 1px solid rgba(255, 255, 255, 0.16);
            border-radius: 50%;
            box-shadow: 0 0 0 28px rgba(255, 255, 255, 0.03),
                        0 0 0 58px rgba(255, 255, 255, 0.025);
        }

        .hero-kicker {
            position: relative;
            z-index: 1;
            margin-bottom: 0.7rem;
            color: #bfdbfe;
            font-size: 0.73rem;
            font-weight: 750;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .hero-title {
            position: relative;
            z-index: 1;
            max-width: 750px;
            margin: 0;
            color: #ffffff !important;
            font-size: clamp(2rem, 4vw, 3.35rem);
            font-weight: 780;
            line-height: 1.04;
            letter-spacing: -0.055em;
        }

        .hero-copy {
            position: relative;
            z-index: 1;
            max-width: 690px;
            margin: 1rem 0 0;
            color: #cbd5e1;
            font-size: 1rem;
            line-height: 1.65;
        }

        .hero-tags {
            position: relative;
            z-index: 1;
            display: flex;
            flex-wrap: wrap;
            gap: 0.55rem;
            margin-top: 1.35rem;
        }

        .hero-tag {
            padding: 0.42rem 0.68rem;
            border: 1px solid rgba(191, 219, 254, 0.23);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.08);
            color: #dbeafe;
            font-size: 0.75rem;
            font-weight: 600;
        }

        .workspace-heading {
            display: flex;
            align-items: end;
            justify-content: space-between;
            gap: 1rem;
            margin: 2.1rem 0 0.9rem;
        }

        .eyebrow {
            margin-bottom: 0.32rem;
            color: var(--blue);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.13em;
            text-transform: uppercase;
        }

        .section-title {
            margin: 0;
            font-size: 1.55rem;
            font-weight: 760;
            letter-spacing: -0.04em;
        }

        .section-note {
            max-width: 540px;
            margin: 0.45rem 0 0;
            color: var(--muted);
            font-size: 0.91rem;
            line-height: 1.55;
        }

        .surface {
            padding: 1.3rem 1.35rem;
            border: 1px solid rgba(226, 232, 240, 0.9);
            border-radius: 16px;
            background: rgba(255, 255, 255, 0.82);
            box-shadow: var(--shadow);
        }

        .surface-title {
            margin: 0 0 0.25rem;
            color: var(--ink);
            font-size: 0.98rem;
            font-weight: 750;
        }

        .surface-copy {
            margin: 0 0 0.9rem;
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .workflow-list {
            display: grid;
            gap: 0.7rem;
            margin-top: 0.85rem;
        }

        .workflow-item {
            display: flex;
            align-items: center;
            gap: 0.72rem;
            color: var(--ink-soft);
            font-size: 0.82rem;
        }

        .workflow-number {
            display: grid;
            flex: 0 0 auto;
            width: 27px;
            height: 27px;
            place-items: center;
            border-radius: 9px;
            background: var(--blue-soft);
            color: var(--blue);
            font-size: 0.72rem;
            font-weight: 800;
        }

        div[data-testid="stTextArea"] textarea,
        div[data-testid="stTextInput"] input {
            min-height: 52px;
            border: 1px solid #cbd5e1;
            border-radius: 12px;
            background: #ffffff;
            color: var(--ink);
            font-size: 0.96rem;
            box-shadow: 0 4px 14px rgba(15, 23, 42, 0.04);
        }

        div[data-testid="stTextArea"] textarea:focus,
        div[data-testid="stTextInput"] input:focus {
            border-color: var(--blue);
            box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.13);
        }

        div[data-testid="stTextArea"] label,
        div[data-testid="stTextInput"] label {
            color: var(--ink-soft);
            font-size: 0.82rem;
            font-weight: 700;
        }

        .stButton > button {
            min-height: 44px;
            border-radius: 11px;
            border: 1px solid #cbd5e1;
            color: var(--ink-soft);
            background: #ffffff;
            font-weight: 700;
            transition: all 0.18s ease;
        }

        .stButton > button:hover {
            border-color: var(--blue);
            color: var(--blue);
            box-shadow: 0 6px 18px rgba(37, 99, 235, 0.12);
        }

        .stButton > button[kind="primary"] {
            border: 0;
            color: #ffffff;
            background: linear-gradient(135deg, #2563eb 0%, #4f46e5 100%);
            box-shadow: 0 10px 20px rgba(37, 99, 235, 0.22);
        }

        .stButton > button[kind="primary"]:hover {
            color: #ffffff;
            background: linear-gradient(135deg, #1d4ed8 0%, #4338ca 100%);
            box-shadow: 0 12px 24px rgba(37, 99, 235, 0.28);
            transform: translateY(-1px);
        }

        [data-baseweb="tab-list"] {
            gap: 0.45rem;
            padding: 0.35rem;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: rgba(241, 245, 249, 0.78);
        }

        [data-baseweb="tab"] {
            height: 42px;
            padding: 0 1.05rem;
            border-radius: 9px;
            color: var(--muted);
            font-size: 0.82rem;
            font-weight: 700;
        }

        [aria-selected="true"][data-baseweb="tab"] {
            color: var(--ink);
            background: #ffffff;
            box-shadow: 0 3px 12px rgba(15, 23, 42, 0.08);
        }

        [data-baseweb="tab-highlight"] {
            display: none;
        }

        .metric-row {
            display: grid;
            grid-template-columns: repeat(7, minmax(0, 1fr));
            gap: 0.72rem;
            margin: 1rem 0 1.4rem;
        }

        .metric-card {
            min-height: 88px;
            padding: 0.9rem 0.95rem;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #ffffff;
            box-shadow: 0 5px 16px rgba(15, 23, 42, 0.04);
        }

        .metric-value {
            color: var(--ink);
            font-size: 1.45rem;
            font-weight: 800;
            line-height: 1;
        }

        .metric-label {
            margin-top: 0.48rem;
            color: var(--muted);
            font-size: 0.67rem;
            font-weight: 750;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .status-banner {
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            margin: 1rem 0 0.85rem;
            padding: 0.9rem 1rem;
            border: 1px solid #dbeafe;
            border-radius: 13px;
            background: linear-gradient(90deg, #eff6ff 0%, #f5f3ff 100%);
        }

        .status-label {
            color: var(--muted);
            font-size: 0.76rem;
            font-weight: 700;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }

        .status-value {
            color: var(--ink);
            font-size: 0.92rem;
            font-weight: 800;
        }

        .badge {
            display: inline-flex;
            align-items: center;
            padding: 0.3rem 0.58rem;
            border: 1px solid transparent;
            border-radius: 999px;
            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.06em;
            text-transform: uppercase;
            white-space: nowrap;
        }

        .badge-corroborated { color: var(--green); background: var(--green-soft); border-color: #bbf7d0; }
        .badge-contested { color: var(--red); background: var(--red-soft); border-color: #fecaca; }
        .badge-single_source { color: var(--amber); background: var(--amber-soft); border-color: #fde68a; }
        .badge-domain { color: #4338ca; background: #eef2ff; border-color: #c7d2fe; }

        .stepper-wrap {
            position: relative;
            overflow-x: auto;
            padding: 0.95rem 0.2rem 0.7rem;
            margin-bottom: 0.8rem;
        }

        .stepper {
            display: flex;
            min-width: 650px;
            justify-content: space-between;
            position: relative;
            z-index: 2;
        }

        .step {
            flex: 1;
            min-width: 125px;
            text-align: center;
        }

        .step-circle {
            display: grid;
            width: 36px;
            height: 36px;
            place-items: center;
            margin: 0 auto 0.55rem;
            border: 2px solid #cbd5e1;
            border-radius: 50%;
            background: #ffffff;
            color: var(--muted);
            font-size: 0.74rem;
            font-weight: 800;
        }

        .step.done .step-circle {
            border-color: var(--blue);
            color: #ffffff;
            background: var(--blue);
        }

        .step.active .step-circle {
            border-color: var(--violet);
            color: var(--violet);
            box-shadow: 0 0 0 5px rgba(124, 58, 237, 0.12);
        }

        .step-label { color: var(--ink-soft); font-size: 0.75rem; font-weight: 750; }
        .step-sub { min-height: 15px; margin-top: 0.2rem; color: var(--muted); font-size: 0.66rem; }
        .stepper-line-base { position: absolute; top: 34px; left: 10%; right: 10%; height: 2px; background: #e2e8f0; z-index: 1; }
        .stepper-line-progress { position: absolute; top: 34px; left: 10%; height: 2px; background: linear-gradient(90deg, var(--blue), var(--violet)); z-index: 1; transition: width 0.3s ease; }

        .concl-index {
            color: var(--blue);
            font-size: 0.69rem;
            font-weight: 850;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .concl-text {
            margin: 0.6rem 0 1rem;
            color: var(--ink);
            font-size: 1.02rem;
            font-weight: 650;
            line-height: 1.55;
        }

        div[data-testid="stExpander"] {
            overflow: hidden;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #ffffff;
        }

        div[data-testid="stExpander"] summary p {
            color: var(--ink-soft);
            font-weight: 700;
        }

        .section-divider {
            height: 1px;
            margin: 1.7rem 0;
            background: var(--line);
        }

        .footer-note {
            margin-top: 2rem;
            color: var(--muted);
            font-size: 0.72rem;
            text-align: center;
        }

        .difference-banner {
            display: grid;
            grid-template-columns: 1.15fr 0.85fr;
            gap: 1rem;
            margin: 1.2rem 0 1.5rem;
            padding: 1.15rem 1.25rem;
            border: 1px solid #c7d2fe;
            border-radius: 16px;
            background: linear-gradient(110deg, #eef2ff 0%, #f8fafc 68%);
        }

        .difference-title {
            margin: 0 0 0.35rem;
            color: #312e81;
            font-size: 0.98rem;
            font-weight: 800;
        }

        .difference-copy {
            margin: 0;
            color: var(--ink-soft);
            font-size: 0.82rem;
            line-height: 1.55;
        }

        .difference-list {
            display: grid;
            gap: 0.45rem;
            align-content: center;
        }

        .difference-item {
            display: flex;
            gap: 0.55rem;
            align-items: center;
            color: var(--ink-soft);
            font-size: 0.76rem;
            font-weight: 650;
        }

        .difference-check {
            display: grid;
            flex: 0 0 auto;
            width: 20px;
            height: 20px;
            place-items: center;
            border-radius: 6px;
            color: #ffffff;
            background: #4f46e5;
            font-size: 0.7rem;
            font-weight: 800;
        }

        .signal-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.75rem 0 1.35rem;
        }

        .signal-card {
            min-height: 106px;
            padding: 0.95rem 1rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
            box-shadow: 0 5px 16px rgba(15, 23, 42, 0.04);
        }

        .exec-hero {
            margin: 0.95rem 0 0.8rem;
            padding: 1.2rem 1.3rem;
            border: 1px solid #c7d2fe;
            border-radius: 17px;
            background: linear-gradient(110deg, #eef2ff 0%, #ffffff 72%);
            box-shadow: 0 8px 24px rgba(37, 99, 235, 0.08);
        }

        .exec-kicker {
            color: #4338ca !important;
            font-size: 0.66rem;
            font-weight: 850;
            letter-spacing: 0.1em;
            text-transform: uppercase;
        }

        .exec-headline {
            max-width: 940px;
            margin-top: 0.42rem;
            color: #0f172a !important;
            font-size: 1.35rem;
            font-weight: 820;
            line-height: 1.3;
        }

        .exec-subline {
            margin-top: 0.48rem;
            color: #475569 !important;
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .exec-kpi-row {
            display: grid;
            grid-template-columns: repeat(4, minmax(0, 1fr));
            gap: 0.7rem;
            margin: 0.8rem 0 1rem;
        }

        .exec-kpi {
            min-height: 84px;
            padding: 0.82rem 0.9rem;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #ffffff;
            box-shadow: 0 5px 16px rgba(15, 23, 42, 0.04);
        }

        .exec-kpi-value {
            color: #0f172a !important;
            font-size: 1.38rem;
            font-weight: 850;
            line-height: 1;
        }

        .exec-kpi-label {
            margin-top: 0.4rem;
            color: #475569 !important;
            font-size: 0.65rem;
            font-weight: 800;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .exec-insight-grid {
            display: grid;
            grid-template-columns: repeat(3, minmax(0, 1fr));
            gap: 0.75rem;
            margin: 0.7rem 0 1.15rem;
        }

        .exec-insight-card {
            min-height: 108px;
            padding: 0.9rem 0.95rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
        }

        .exec-insight-label {
            color: #64748b !important;
            font-size: 0.65rem;
            font-weight: 850;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .exec-insight-title {
            margin-top: 0.35rem;
            color: #0f172a !important;
            font-size: 0.88rem;
            font-weight: 800;
            line-height: 1.3;
        }

        .exec-insight-copy {
            margin-top: 0.28rem;
            color: #475569 !important;
            font-size: 0.75rem;
            line-height: 1.4;
        }

        .exec-section-title {
            margin: 1.15rem 0 0.18rem;
            color: #0f172a !important;
            font-size: 1.02rem;
            font-weight: 820;
        }

        .exec-section-note {
            margin: 0 0 0.55rem;
            color: #64748b !important;
            font-size: 0.77rem;
        }

        .exec-event-strip {
            display: grid;
            grid-template-columns: repeat(5, minmax(0, 1fr));
            gap: 0.55rem;
            margin: 0.65rem 0 1rem;
        }

        .exec-event-card {
            min-height: 78px;
            padding: 0.72rem 0.78rem;
            border: 1px solid var(--line);
            border-radius: 12px;
            background: #ffffff;
            box-shadow: 0 4px 13px rgba(15, 23, 42, 0.04);
        }

        .exec-event-top {
            display: flex;
            align-items: center;
            gap: 0.38rem;
            color: #64748b !important;
            font-size: 0.61rem;
            font-weight: 800;
            letter-spacing: 0.05em;
            text-transform: uppercase;
        }

        .exec-event-dot {
            width: 8px;
            height: 8px;
            flex: 0 0 auto;
            border-radius: 50%;
        }

        .exec-event-high { background: #dc2626; }
        .exec-event-medium { background: #d97706; }
        .exec-event-low { background: #2563eb; }

        .exec-event-date { color: #334155 !important; }
        .exec-event-kind { color: #64748b !important; }
        .exec-event-title {
            margin-top: 0.43rem;
            color: #0f172a !important;
            font-size: 0.76rem;
            font-weight: 800;
            line-height: 1.3;
        }

        .signal-kicker {
            color: var(--muted);
            font-size: 0.66rem;
            font-weight: 800;
            letter-spacing: 0.09em;
            text-transform: uppercase;
        }

        .signal-value {
            margin-top: 0.3rem;
            color: var(--ink);
            font-size: 1.36rem;
            font-weight: 820;
        }

        .signal-detail {
            margin-top: 0.25rem;
            color: var(--muted);
            font-size: 0.73rem;
            line-height: 1.35;
        }

        .claim-panel {
            margin: 0.85rem 0;
            padding: 0.9rem 1rem;
            border: 1px solid var(--line);
            border-radius: 11px;
            background: #f8fafc;
        }

        .claim-panel-a { border-left: 4px solid #2563eb; }
        .claim-panel-b { border-left: 4px solid #c026d3; }

        .claim-label {
            color: var(--muted);
            font-size: 0.67rem;
            font-weight: 800;
            letter-spacing: 0.08em;
            text-transform: uppercase;
        }

        .claim-text {
            margin-top: 0.35rem;
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 700;
            line-height: 1.45;
        }

        .claim-detail {
            margin-top: 0.35rem;
            color: var(--ink-soft);
            font-size: 0.78rem;
            line-height: 1.45;
        }

        .source-meta {
            margin-top: 0.55rem;
            color: var(--muted);
            font-size: 0.7rem;
            line-height: 1.4;
        }

        .source-meta a { color: var(--blue); word-break: break-word; }

        /* Explicit contrast reset for Streamlit-rendered markdown, captions, tables, and links. */
        [data-testid="stMarkdownContainer"],
        [data-testid="stMarkdownContainer"] p,
        [data-testid="stMarkdownContainer"] li,
        [data-testid="stMarkdownContainer"] span,
        [data-testid="stMarkdownContainer"] strong,
        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p,
        [data-testid="stDataFrame"],
        [data-testid="stDataFrame"] * {
            color: #0f172a !important;
        }

        [data-testid="stCaptionContainer"],
        [data-testid="stCaptionContainer"] p {
            color: #475569 !important;
        }

        [data-testid="stMarkdownContainer"] .hero,
        [data-testid="stMarkdownContainer"] .hero * { color: #ffffff !important; }
        [data-testid="stMarkdownContainer"] .hero-kicker { color: #bfdbfe !important; }
        [data-testid="stMarkdownContainer"] .hero-copy { color: #cbd5e1 !important; }
        [data-testid="stMarkdownContainer"] .hero-tag { color: #dbeafe !important; }
        .eyebrow { color: var(--blue) !important; }
        .badge { color: inherit !important; }
        .badge-corroborated { color: var(--green) !important; }
        .badge-contested { color: var(--red) !important; }
        .badge-single_source { color: var(--amber) !important; }
        .badge-domain { color: #4338ca !important; }
        .difference-title { color: #312e81 !important; }
        .difference-copy, .difference-item { color: var(--ink-soft) !important; }
        .signal-kicker, .signal-detail, .claim-label, .claim-detail, .source-meta { color: var(--muted) !important; }
        .signal-value, .claim-text, .chart-title { color: var(--ink) !important; }

        .major-timeline {
            position: relative;
            margin: 0.85rem 0 1.25rem;
            padding: 0.45rem 0 0.25rem;
        }

        .major-timeline::before {
            content: "";
            position: absolute;
            top: 0.8rem;
            bottom: 0.8rem;
            left: 17px;
            width: 2px;
            background: linear-gradient(180deg, #93c5fd 0%, #c4b5fd 100%);
        }

        .timeline-item {
            position: relative;
            display: grid;
            grid-template-columns: 36px minmax(0, 1fr);
            gap: 0.95rem;
            margin-bottom: 0.8rem;
        }

        .timeline-marker {
            position: relative;
            z-index: 1;
            width: 35px;
            height: 35px;
            display: grid;
            place-items: center;
            border: 4px solid #f8fafc;
            border-radius: 50%;
            color: #ffffff !important;
            font-size: 0.58rem;
            font-weight: 850;
        }

        .timeline-high { background: #dc2626; box-shadow: 0 0 0 1px #fecaca; }
        .timeline-medium { background: #d97706; box-shadow: 0 0 0 1px #fde68a; }
        .timeline-low { background: #2563eb; box-shadow: 0 0 0 1px #bfdbfe; }

        .timeline-card {
            padding: 0.85rem 0.95rem;
            border: 1px solid var(--line);
            border-radius: 13px;
            background: #ffffff;
            box-shadow: 0 5px 16px rgba(15, 23, 42, 0.04);
        }

        .timeline-meta {
            color: var(--blue) !important;
            font-size: 0.67rem;
            font-weight: 850;
            letter-spacing: 0.07em;
            text-transform: uppercase;
        }

        .timeline-title {
            margin-top: 0.28rem;
            color: var(--ink) !important;
            font-size: 0.94rem;
            font-weight: 800;
            line-height: 1.35;
        }

        .timeline-description {
            margin-top: 0.35rem;
            color: var(--ink-soft) !important;
            font-size: 0.8rem;
            line-height: 1.5;
        }

        .timeline-source {
            margin-top: 0.55rem;
            color: var(--muted) !important;
            font-size: 0.7rem;
            line-height: 1.4;
        }

        .timeline-source a { color: var(--blue) !important; word-break: break-word; }

        .timeline-empty {
            padding: 1rem;
            border: 1px dashed #cbd5e1;
            border-radius: 13px;
            color: var(--ink-soft) !important;
            background: #f8fafc;
            font-size: 0.82rem;
            line-height: 1.5;
        }

        .chart-surface {
            padding: 0.9rem 1rem 0.35rem;
            border: 1px solid var(--line);
            border-radius: 14px;
            background: #ffffff;
        }

        .chart-title {
            margin: 0;
            color: var(--ink);
            font-size: 0.9rem;
            font-weight: 800;
        }

        .chart-caption {
            margin: 0.3rem 0 0;
            color: var(--muted);
            font-size: 0.73rem;
            line-height: 1.4;
        }

        @media (max-width: 900px) {
            .block-container { padding-top: 1.35rem; }
            .topbar { align-items: flex-start; }
            .status-pill { display: none; }
            .hero { padding: 1.55rem 1.25rem; border-radius: 18px; }
            .metric-row { grid-template-columns: repeat(2, minmax(0, 1fr)); }
            .exec-kpi-row, .exec-insight-grid { grid-template-columns: 1fr 1fr; }
            .exec-event-strip { grid-template-columns: 1fr 1fr; }
            .workspace-heading { display: block; }
            .difference-banner { grid-template-columns: 1fr; }
            .signal-grid { grid-template-columns: 1fr; }
            .timeline-item { grid-template-columns: 30px minmax(0, 1fr); gap: 0.7rem; }
            .timeline-marker { width: 30px; height: 30px; }
            .major-timeline::before { left: 14px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_topbar():
    st.markdown(
        """
        <div class="topbar">
            <div class="brand-lockup">
                <div class="brand-mark">AI</div>
                <div>
                    <div class="brand-name">MODUS RESEARCH INTELLIGENCE</div>
                    <div class="brand-subtitle">Enterprise evidence, built for decisions</div>
                </div>
            </div>
            <div class="status-pill"><span class="status-dot"></span>Research engine ready</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_hero():
    st.markdown(
        """
        <section class="hero">
            <div class="hero-kicker">Modus AI · Assignment 09</div>
            <h1 class="hero-title">Turn a question into an evidence-backed research dossier.</h1>
            <p class="hero-copy">
                Explore any industry with a transparent multi-agent pipeline that plans the research,
                gathers sources, compares evidence, detects contradictions, and preserves every conclusion's provenance.
            </p>
            <div class="hero-tags">
                <span class="hero-tag">Dynamic research planning</span>
                <span class="hero-tag">Structured evidence</span>
                <span class="hero-tag">Full traceability</span>
            </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- pipeline and result components
PIPELINE_STAGES = [
    {"key": "classify", "num": "01", "label": "Classify & plan", "event_stages": {"classify"}},
    {"key": "search", "num": "02", "label": "Search & collect", "event_stages": {"search", "collect"}},
    {"key": "extract", "num": "03", "label": "Extract findings", "event_stages": {"extract"}},
    {"key": "compare", "num": "04", "label": "Compare evidence", "event_stages": {"compare", "contradictions"}},
    {"key": "synthesize", "num": "05", "label": "Synthesize", "event_stages": {"synthesize", "done"}},
]


def render_stepper(events: list[dict], status: str):
    seen_stages = {event["stage"] for event in events}
    stage_counts: dict[str, int] = {}
    for event in events:
        stage_counts[event["stage"]] = stage_counts.get(event["stage"], 0) + 1

    reached_idx = -1
    for index, stage in enumerate(PIPELINE_STAGES):
        if stage["event_stages"] & seen_stages:
            reached_idx = index

    steps_html = []
    for index, stage in enumerate(PIPELINE_STAGES):
        touched = bool(stage["event_stages"] & seen_stages)
        active = index == reached_idx and status in {"running", "failed"}
        if status == "done" and touched:
            css_class = "done"
        elif active:
            css_class = "active"
        elif touched:
            css_class = "done"
        else:
            css_class = ""

        event_count = sum(stage_counts.get(name, 0) for name in stage["event_stages"])
        sub_text = f"{event_count} event(s)" if event_count else "Waiting"
        steps_html.append(
            f'<div class="step {css_class}">'
            f'<div class="step-circle">{stage["num"]}</div>'
            f'<div class="step-label">{stage["label"]}</div>'
            f'<div class="step-sub">{sub_text}</div>'
            f'</div>'
        )

    stage_count = len(PIPELINE_STAGES)
    progress_ratio = max(reached_idx, 0) / (stage_count - 1) if reached_idx >= 0 else 0.0
    if status == "done":
        progress_ratio = 1.0
    progress_pct = round(progress_ratio * 80, 1)

    st.markdown(
        f"""
        <div class="stepper-wrap">
            <div class="stepper-line-base"></div>
            <div class="stepper-line-progress" style="width:{progress_pct}%;"></div>
            <div class="stepper">{''.join(steps_html)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


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
        f'<div class="metric-card"><div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div></div>'
        for label, value in items
    )
    st.markdown(f'<div class="metric-row">{cards}</div>', unsafe_allow_html=True)


def render_classification_chart(stats: dict):
    labels = ["Corroborated", "Single source", "Contested"]
    values = [stats["corroborated_count"], stats["single_source_count"], stats["contested_count"]]
    colors = ["#15803d", "#a16207", "#b91c1c"]
    if sum(values) == 0:
        st.info("Evidence classifications will appear when findings are available.")
        return

    figure = go.Figure(
        go.Bar(
            x=values,
            y=labels,
            orientation="h",
            marker_color=colors,
            text=values,
            textposition="outside",
            hovertemplate="%{y}: %{x}<extra></extra>",
        )
    )
    figure.update_layout(
        height=190,
        margin=dict(l=8, r=35, t=12, b=8),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=12, color="#0f172a"),
        xaxis=dict(showgrid=False, zeroline=False, visible=False),
        yaxis=dict(showgrid=False),
        showlegend=False,
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_difference_banner():
    st.markdown(
        """
        <div class="difference-banner">
            <div>
                <div class="difference-title">This is not a chat answer. It is a research asset.</div>
                <p class="difference-copy">
                    ChatGPT can produce a persuasive summary. Modus builds a reusable evidence layer:
                    every claim is classified, every disagreement is preserved, source coverage is visible,
                    and decision signals are calculated from the stored research graph.
                </p>
            </div>
            <div class="difference-list">
                <div class="difference-item"><span class="difference-check">✓</span>Claim-level evidence comparison</div>
                <div class="difference-item"><span class="difference-check">✓</span>Contradictions shown side by side</div>
                <div class="difference-item"><span class="difference-check">✓</span>Research coverage by theme</div>
                <div class="difference-item"><span class="difference-check">✓</span>Reusable signals across future runs</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_decision_signal_board(analytics: dict):
    signals = analytics.get("decision_signals", {}) if analytics else {}
    strongest = signals.get("strongest_evidence", [])
    needs_review = signals.get("needs_review", [])
    gaps = signals.get("coverage_gaps", [])
    cards = [
        ("Strongest evidence", len(strongest), "themes with corroborated support", strongest[0] if strongest else "No corroborated theme yet"),
        ("Needs review", len(needs_review), "themes containing contested evidence", needs_review[0] if needs_review else "No direct conflict detected"),
        ("Coverage gaps", len(gaps), "themes needing more corroboration", gaps[0] if gaps else "All themes have findings"),
    ]
    cards_html = "".join(
        f'<div class="signal-card"><div class="signal-kicker">{escape(label)}</div>'
        f'<div class="signal-value">{value}</div><div class="signal-detail">{escape(detail)} · {escape(example)}</div></div>'
        for label, value, detail, example in cards
    )
    st.markdown(f'<div class="signal-grid">{cards_html}</div>', unsafe_allow_html=True)


def _chart_layout(height: int = 260):
    return dict(
        height=height,
        margin=dict(l=8, r=24, t=18, b=12),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", size=11, color="#0f172a"),
        legend=dict(orientation="h", y=1.12, x=0, bgcolor="rgba(0,0,0,0)"),
    )


def render_theme_evidence_chart(analytics: dict):
    rows = analytics.get("sub_question_breakdown", []) if analytics else []
    rows = [row for row in rows if row.get("finding_count", 0)]
    if not rows:
        st.info("Theme-level evidence will appear after findings are extracted.")
        return

    labels = [row["sub_question"][:52] + ("…" if len(row["sub_question"]) > 52 else "") for row in rows]
    figure = go.Figure()
    for key, label, color in [
        ("corroborated_count", "Corroborated", "#15803d"),
        ("single_source_count", "Single source", "#a16207"),
        ("contested_count", "Contested", "#b91c1c"),
    ]:
        figure.add_trace(
            go.Bar(
                name=label,
                y=labels,
                x=[row.get(key, 0) for row in rows],
                orientation="h",
                marker_color=color,
                hovertemplate=f"{label}: %{{x}}<extra></extra>",
            )
        )
    figure.update_layout(**_chart_layout(max(300, 78 * len(rows))), barmode="stack", xaxis=dict(showgrid=False, title="Findings", tickfont=dict(color="#334155"), title_font=dict(color="#334155")), yaxis=dict(showgrid=False, tickfont=dict(color="#334155"), title_font=dict(color="#334155")))
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_source_portfolio_chart(analytics: dict):
    source_types = analytics.get("source_type_counts", {}) if analytics else {}
    source_types = {label: value for label, value in source_types.items() if value}
    if not source_types:
        st.info("Source portfolio data will appear after sources are collected.")
        return

    figure = go.Figure(
        go.Pie(
            labels=list(source_types.keys()),
            values=list(source_types.values()),
            hole=0.62,
            textinfo="label+percent",
            textposition="outside",
            marker=dict(colors=["#2563eb", "#7c3aed", "#0f766e", "#a16207", "#64748b"]),
            hovertemplate="%{label}: %{value} sources<extra></extra>",
        )
    )
    figure.update_layout(**_chart_layout(300), showlegend=False)
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})


def render_timeline_chart(analytics: dict):
    timeline = analytics.get("timeline", []) if analytics else []
    coverage = analytics.get("date_coverage_percent", 0) if analytics else 0
    if not timeline:
        st.info(
            "No publisher dates were available for this run. The system will show a historical evidence trend "
            "when retrieved sources expose publication metadata."
        )
        return

    years = [point["year"] for point in timeline]
    figure = go.Figure()
    figure.add_trace(
        go.Scatter(
            x=years,
            y=[point["source_count"] for point in timeline],
            name="Sources",
            mode="lines+markers",
            line=dict(color="#2563eb", width=3),
            marker=dict(size=8),
            hovertemplate="%{x}: %{y} sources<extra></extra>",
        )
    )
    figure.add_trace(
        go.Scatter(
            x=years,
            y=[point["corroborated_count"] for point in timeline],
            name="Corroborated findings",
            mode="lines+markers",
            line=dict(color="#15803d", width=3),
            marker=dict(size=8),
            hovertemplate="%{x}: %{y} corroborated findings<extra></extra>",
        )
    )
    figure.update_layout(
        **_chart_layout(300),
        xaxis=dict(showgrid=False, dtick=1, title="Publication year", tickfont=dict(color="#334155"), title_font=dict(color="#334155")),
        yaxis=dict(showgrid=True, gridcolor="#e2e8f0", title="Evidence volume", tickfont=dict(color="#334155"), title_font=dict(color="#334155")),
    )
    st.plotly_chart(figure, use_container_width=True, config={"displayModeBar": False})
    st.caption(f"Historical view based on publisher dates for {coverage:.0f}% of collected sources; undated sources are excluded.")


def render_major_events_timeline(analytics: dict):
    events = analytics.get("timeline_events", []) if analytics else []
    if not events:
        st.markdown(
            """
            <div class="timeline-empty">
                No explicitly dated major events were extracted for this run. The timeline only shows milestones
                that a source page states with a date or year; it never fills gaps with invented historical events.
                Try a question that includes market launches, regulation, company moves, or technology adoption.
            </div>
            """,
            unsafe_allow_html=True,
        )
        return

    items = []
    for event in events:
        impact = str(event.get("impact_level") or "medium").lower()
        if impact not in {"high", "medium", "low"}:
            impact = "medium"
        event_type = escape(str(event.get("event_type") or "milestone").replace("_", " "))
        event_date = escape(str(event.get("event_date") or "Date unavailable"))
        title = escape(str(event.get("title") or "Untitled milestone"))
        description = escape(str(event.get("description") or ""))
        rationale = escape(str(event.get("impact_rationale") or ""))
        source_title = escape(str(event.get("source_title") or event.get("source_domain") or "Source"))
        source_domain = escape(str(event.get("source_domain") or ""))
        source_url = event.get("source_url") or ""
        safe_url = escape(source_url, quote=True)
        description_html = f'<div class="timeline-description">{description}</div>' if description else ""
        rationale_html = f'<span>Impact lens: {rationale}</span>' if rationale else ""
        items.append(
            f'<div class="timeline-item"><div class="timeline-marker timeline-{impact}">{impact[:1].upper()}</div>'
            f'<div class="timeline-card"><div class="timeline-meta">{event_date} · {event_type} · {impact} impact</div>'
            f'<div class="timeline-title">{title}</div>{description_html}'
            f'<div class="timeline-source"><strong>{source_title}</strong> · {source_domain}<br>'
            f'{rationale_html}<br><a href="{safe_url}" target="_blank">Open source evidence ↗</a></div>'
            f'</div></div>'
        )
    st.markdown(f"<div class=\"major-timeline\">{''.join(items)}</div>", unsafe_allow_html=True)


def _clip(value: str, limit: int = 190) -> str:
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def render_compact_event_strip(analytics: dict, limit: int = 5):
    events = (analytics or {}).get("timeline_events", [])[:limit]
    if not events:
        st.markdown(
            '<div class="timeline-empty">No dated milestones were found in this run. The detailed evidence view remains available below.</div>',
            unsafe_allow_html=True,
        )
        return

    cards = []
    for event in events:
        impact = str(event.get("impact_level") or "medium").lower()
        if impact not in {"high", "medium", "low"}:
            impact = "medium"
        date = escape(str(event.get("event_date") or "Date unavailable"))
        title = escape(str(event.get("title") or "Untitled milestone"))
        kind = escape(str(event.get("event_type") or "milestone").replace("_", " "))
        cards.append(
            f'<div class="exec-event-card"><div class="exec-event-top"><span class="exec-event-dot exec-event-{impact}"></span>'
            f'<span class="exec-event-date">{date}</span><span class="exec-event-kind">{kind}</span></div>'
            f'<div class="exec-event-title">{title}</div></div>'
        )
    st.markdown(f'<div class="exec-event-strip">{"".join(cards)}</div>', unsafe_allow_html=True)


def render_executive_summary(detail: dict, analytics: dict):
    stats = detail.get("stats", {})
    conclusions = detail.get("conclusions", [])
    rows = [row for row in (analytics or {}).get("sub_question_breakdown", []) if row.get("finding_count", 0)]
    signals = (analytics or {}).get("decision_signals", {})
    strongest = signals.get("strongest_evidence", [])
    gaps = signals.get("coverage_gaps", [])
    needs_review = signals.get("needs_review", [])

    headline = _clip(conclusions[0].get("text") if conclusions else "The research run did not produce a clear headline conclusion.", 230)
    findings = stats.get("finding_count", 0)
    corroborated = stats.get("corroborated_count", 0)
    support_rate = round((corroborated / findings) * 100) if findings else 0
    event_count = (analytics or {}).get("timeline_event_count", 0)
    source_count = stats.get("source_count", 0)
    domain = escape(str(detail.get("domain") or "general research"))

    st.markdown(
        f'<div class="exec-hero"><div class="exec-kicker">Executive readout · {domain}</div>'
        f'<div class="exec-headline">{escape(headline)}</div>'
        f'<div class="exec-subline">A fast view of what the evidence says, where the impact is concentrated, and what still needs review.</div></div>',
        unsafe_allow_html=True,
    )

    kpis = [
        (support_rate, "corroborated support", "%"),
        (source_count, "sources reviewed", ""),
        (event_count, "dated milestones", ""),
        (stats.get("contradiction_count", 0), "open conflicts", ""),
    ]
    kpi_html = "".join(
        f'<div class="exec-kpi"><div class="exec-kpi-value">{value}{suffix}</div><div class="exec-kpi-label">{label}</div></div>'
        for value, label, suffix in kpis
    )
    st.markdown(f'<div class="exec-kpi-row">{kpi_html}</div>', unsafe_allow_html=True)

    strongest_text = _clip(strongest[0], 105) if strongest else "No theme has enough corroboration yet."
    gap_text = _clip(gaps[0], 105) if gaps else "No major coverage gap was flagged."
    review_text = _clip(needs_review[0], 105) if needs_review else ("No direct conflict detected." if not stats.get("contradiction_count") else "Review the open evidence conflicts.")
    insight_cards = [
        ("Strongest area", strongest_text, "Most supported theme"),
        ("Watch next", gap_text, "Where more research is needed"),
        ("Risk signal", review_text, "What may change the conclusion"),
    ]
    insight_html = "".join(
        f'<div class="exec-insight-card"><div class="exec-insight-label">{label}</div>'
        f'<div class="exec-insight-title">{escape(title)}</div><div class="exec-insight-copy">{escape(copy)}</div></div>'
        for label, title, copy in insight_cards
    )
    st.markdown(f'<div class="exec-insight-grid">{insight_html}</div>', unsafe_allow_html=True)

    st.markdown('<div class="exec-section-title">Impact map</div><div class="exec-section-note">Two visuals answer “where is the impact?” and “what is the evidence made of?”</div>', unsafe_allow_html=True)
    chart_col, source_col = st.columns([1.28, 0.72], gap="large")
    with chart_col:
        render_theme_evidence_chart(analytics)
    with source_col:
        render_source_portfolio_chart(analytics)

    st.markdown(f'<div class="exec-section-title">What changed over time · {event_count} milestones</div><div class="exec-section-note">A compact chronology of the most important dated events; open the detail view for full provenance.</div>', unsafe_allow_html=True)
    render_compact_event_strip(analytics)

    if rows:
        top_theme = max(rows, key=lambda row: row.get("corroborated_count", 0))
        st.caption(f"Most supported theme: {_clip(top_theme.get('sub_question', ''), 150)}")


def render_detailed_dossier(detail: dict, analytics: dict, topic_id: int):
    render_metric_row(detail["stats"])
    render_difference_banner()
    render_decision_signal_board(analytics)

    evidence_col, source_col = st.columns([1.25, 0.75], gap="large")
    with evidence_col:
        st.markdown("#### Evidence by research theme")
        st.caption("This shows where the pipeline has strong, single-source, or disputed coverage.")
        render_theme_evidence_chart(analytics)
    with source_col:
        st.markdown("#### Source portfolio")
        st.caption("A transparent view of the source mix behind the dossier.")
        render_source_portfolio_chart(analytics)

    event_count = analytics.get("timeline_event_count", 0)
    st.markdown(f"#### Major events & market milestones · {event_count}")
    st.caption("Dated launches, regulations, company moves, market events, and adoption milestones extracted from the research sources.")
    render_major_events_timeline(analytics)

    st.markdown("#### Research horizon")
    st.caption("Publication-year signals separate current evidence from historical context without inventing dates.")
    render_timeline_chart(analytics)

    st.markdown("### Evidence profile")
    chart_col, insight_col = st.columns([1.15, 0.85], gap="large")
    with chart_col:
        render_classification_chart(detail["stats"])
    with insight_col:
        st.markdown(
            """
            <div class="surface">
                <p class="surface-copy">
                    <strong>Corroborated</strong> findings are supported by more than one source.
                    <strong>Contested</strong> findings contain disagreement. <strong>Single-source</strong>
                    findings are useful signals that still need additional confirmation.
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    st.markdown("### Conclusions")
    st.caption("Each conclusion is linked to the findings and source URLs that support it.")
    for index, conclusion in enumerate(detail["conclusions"], start=1):
        render_conclusion_card(index, conclusion)

    if detail["contradictions"]:
        st.markdown("### Contradictions detected")
        st.caption("These source-level disagreements are retained as structured evidence.")
        for contradiction in detail["contradictions"]:
            render_contradiction_card(contradiction)

    st.markdown("### Complete findings")
    st.caption("Every extracted finding is grouped by the sub-question it answers.")
    for group in detail["findings_by_sub_question"]:
        st.markdown(
            f'<div class="surface-title">{escape(group["sub_question"])} · {len(group["findings"])} findings</div>',
            unsafe_allow_html=True,
        )
        if group["findings"]:
            frame = pd.DataFrame(
                [
                    {
                        "Claim": finding["claim"],
                        "Detail": finding["detail"] or "",
                        "Classification": finding["classification"].replace("_", " "),
                        "Source": finding["source_url"],
                    }
                    for finding in group["findings"]
                ]
            )
            st.dataframe(
                frame,
                use_container_width=True,
                hide_index=True,
                column_config={"Source": st.column_config.LinkColumn("Source")},
            )
            st.download_button(
                "Download findings as CSV",
                frame.to_csv(index=False),
                file_name=f"findings_{topic_id}.csv",
                key=f"dl_{group['sub_question'][:20]}_{topic_id}",
            )
        else:
            st.caption("No findings were extracted for this sub-question.")


def _confidence(findings: list[dict]):
    if not findings:
        return "Unverified", "single_source"
    corroborated = sum(1 for finding in findings if finding["classification"] == "corroborated")
    contested = sum(1 for finding in findings if finding["classification"] == "contested")
    if contested > 0 and contested >= corroborated:
        return "Disputed", "contested"
    if corroborated / len(findings) >= 0.5:
        return "Strong evidence", "corroborated"
    return "Limited evidence", "single_source"


def render_conclusion_card(index: int, conclusion: dict):
    label, css_class = _confidence(conclusion["findings"])
    with st.container(border=True):
        st.markdown(
            f'<span class="concl-index">CONCLUSION {index:02d}</span> '
            f'<span class="badge badge-{css_class}">{label}</span>',
            unsafe_allow_html=True,
        )
        st.markdown(f'<div class="concl-text">{conclusion["text"]}</div>', unsafe_allow_html=True)
        frame = pd.DataFrame(
            [
                {
                    "Claim": finding["claim"],
                    "Classification": finding["classification"].replace("_", " "),
                    "Source": finding["source_url"],
                }
                for finding in conclusion["findings"]
            ]
        )
        st.dataframe(
            frame,
            use_container_width=True,
            hide_index=True,
            column_config={"Source": st.column_config.LinkColumn("Source")},
        )


def _render_claim_panel(label: str, finding: dict, css_class: str):
    claim = escape(finding.get("claim") or "No claim text returned.")
    detail = escape(finding.get("detail") or "")
    title = escape(finding.get("source_title") or finding.get("source_domain") or "Source")
    domain = escape(finding.get("source_domain") or "")
    published = escape(finding.get("source_published_date") or "Date unavailable")
    source_type = escape(finding.get("source_type") or "Web source")
    url = finding.get("source_url") or ""
    safe_url = escape(url, quote=True)
    detail_html = f'<div class="claim-detail">{detail}</div>' if detail else ""
    st.markdown(
        f"""
        <div class="claim-panel {css_class}">
            <div class="claim-label">{escape(label)} · {source_type}</div>
            <div class="claim-text">{claim}</div>
            {detail_html}
            <div class="source-meta">
                <strong>{title}</strong> · {domain} · Published: {published}<br>
                <a href="{safe_url}" target="_blank">Open source evidence ↗</a>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_contradiction_card(contradiction: dict):
    explanation = escape(contradiction.get("explanation") or "The sources disagree on this point.")
    with st.container(border=True):
        st.markdown(
            f'<span class="badge badge-contested">Contradiction</span>&nbsp;&nbsp;'
            f'<strong>{explanation}</strong>',
            unsafe_allow_html=True,
        )
        left, right = st.columns(2, gap="large")
        with left:
            _render_claim_panel("Source A", contradiction.get("finding_a", {}), "claim-panel-a")
        with right:
            _render_claim_panel("Source B", contradiction.get("finding_b", {}), "claim-panel-b")


def render_status_banner(detail: dict):
    domain = detail.get("domain")
    status = detail.get("status", "pending").replace("_", " ").title()
    domain_markup = (
        f'<span class="badge badge-domain">{domain}</span>' if domain else "Detecting domain"
    )
    st.markdown(
        f"""
        <div class="status-banner">
            <div><div class="status-label">Run status</div><div class="status-value">{status}</div></div>
            <div><div class="status-label">Research domain</div><div class="status-value">{domain_markup}</div></div>
        </div>
        """,
        unsafe_allow_html=True,
    )


# --------------------------------------------------------------------------- application
inject_base_styles()
render_topbar()
render_hero()

st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
tab_new, tab_kb, tab_about = st.tabs(["Research workspace", "Knowledge base", "Architecture"])


# --------------------------------------------------------------------------- Research workspace
with tab_new:
    st.markdown(
        """
        <div class="workspace-heading">
            <div>
                <div class="eyebrow">Start an investigation</div>
                <h2 class="section-title">What do you need to understand?</h2>
                <p class="section-note">
                    Ask a business research question in plain language. The system will determine the domain,
                    plan the investigation, retrieve evidence, and build a traceable answer.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    input_col, workflow_col = st.columns([1.55, 0.9], gap="large")
    with input_col:
        st.markdown('<div class="surface">', unsafe_allow_html=True)
        question = st.text_area(
            "Research question",
            placeholder="Example: How is AI transforming retail operations?",
            height=118,
            label_visibility="visible",
        )
        submit = st.button("Run evidence-backed research", type="primary", use_container_width=True)
        st.caption("Try a new industry or topic. The pipeline is designed for live, domain-agnostic questions.")
        st.markdown('</div>', unsafe_allow_html=True)

    with workflow_col:
        st.markdown(
            """
            <div class="surface">
                <div class="surface-title">What happens next</div>
                <p class="surface-copy">Every stage produces structured, reviewable output.</p>
                <div class="workflow-list">
                    <div class="workflow-item"><span class="workflow-number">01</span>Classify the domain and plan sub-questions</div>
                    <div class="workflow-item"><span class="workflow-number">02</span>Search and collect relevant source pages</div>
                    <div class="workflow-item"><span class="workflow-number">03</span>Extract and compare discrete findings</div>
                    <div class="workflow-item"><span class="workflow-number">04</span>Synthesize conclusions with provenance</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    if submit and question.strip():
        response = api_post("/research", json={"question": question.strip()})
        st.session_state["active_topic_id"] = response["id"]

    topic_id = st.session_state.get("active_topic_id")
    if topic_id:
        header_box = st.empty()
        stepper_box = st.empty()
        log_box = st.empty()
        results_box = st.empty()

        for _ in range(180):
            detail = api_get(f"/research/{topic_id}")

            with header_box.container():
                render_status_banner(detail)

            with stepper_box.container():
                st.markdown('<div class="surface">', unsafe_allow_html=True)
                render_stepper(detail["events"], detail["status"])
                st.markdown('</div>', unsafe_allow_html=True)

            with log_box.container():
                with st.expander("View activity log", expanded=False):
                    for event in detail["events"]:
                        st.markdown(
                            f'<span class="eyebrow">{event["stage"]}</span>&nbsp;&nbsp;'
                            f'{event["message"]}',
                            unsafe_allow_html=True,
                        )

            if detail["status"] in ("done", "failed"):
                with results_box.container():
                    if detail["status"] == "done":
                        analytics = detail.get("analytics", {})
                        render_executive_summary(detail, analytics)
                        with st.expander("Open detailed evidence dossier", expanded=False):
                            render_detailed_dossier(detail, analytics, topic_id)
                    else:
                        st.error("The research run stopped before producing results. See the activity log for details.")
                break

            time.sleep(2)


# --------------------------------------------------------------------------- Knowledge base
with tab_kb:
    st.markdown(
        """
        <div class="workspace-heading">
            <div>
                <div class="eyebrow">Reusable intelligence</div>
                <h2 class="section-title">Knowledge base</h2>
                <p class="section-note">
                    Browse past investigations and search across every finding collected so far.
                    This is where individual research runs become a reusable intelligence asset.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    topics = api_get("/research", stop_on_error=False)
    st.markdown("#### Past research runs")
    if topics is None:
        st.info("The knowledge base will appear here when the research engine is connected.")
    elif not topics:
        st.info("No research runs yet. Start an investigation in the Research workspace.")
    for topic in topics or []:
        domain_markup = (
            f'<span class="badge badge-domain">{topic.get("domain")}</span>'
            if topic.get("domain")
            else ""
        )
        with st.expander(f'{topic["question"]}  ·  {topic["status"]}'):
            st.markdown(domain_markup, unsafe_allow_html=True)
            detail = api_get(f'/research/{topic["id"]}')
            if detail["status"] == "done":
                render_metric_row(detail["stats"])
                for conclusion in detail["conclusions"]:
                    st.markdown(f'- {conclusion["text"]}')

    st.markdown('<div class="section-divider"></div>', unsafe_allow_html=True)
    st.markdown("#### Search across findings")
    st.caption("Use a concept, business problem, technology, or capability to find related evidence.")
    kb_query = st.text_input(
        "Knowledge-base query",
        key="kb_search",
        placeholder="Example: demand forecasting",
        label_visibility="collapsed",
    )
    if kb_query:
        results = api_get("/knowledge-base/search", params={"q": kb_query})
        if results["results"]:
            frame = pd.DataFrame(
                [
                    {
                        "Finding": hit["text"],
                        "Domain": hit["metadata"].get("domain", ""),
                        "Source": hit["metadata"].get("source_url", ""),
                    }
                    for hit in results["results"]
                ]
            )
            st.dataframe(
                frame,
                use_container_width=True,
                hide_index=True,
                column_config={"Source": st.column_config.LinkColumn("Source")},
            )
        else:
            st.info("No matching findings yet.")


# --------------------------------------------------------------------------- Architecture
with tab_about:
    st.markdown(
        """
        <div class="workspace-heading">
            <div>
                <div class="eyebrow">How it works</div>
                <h2 class="section-title">A transparent research architecture</h2>
                <p class="section-note">
                    The application separates interface, orchestration, intelligence, persistence, and external research
                    so every stage can be inspected and explained.
                </p>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="surface">', unsafe_allow_html=True)
    render_stepper(
        [{"stage": stage, "message": ""} for item in PIPELINE_STAGES for stage in item["event_stages"]],
        status="done",
    )
    st.markdown('</div>', unsafe_allow_html=True)

    architecture_col, principles_col = st.columns([1.1, 0.9], gap="large")
    with architecture_col:
        st.markdown(
            """
            | Layer | Component | Role |
            |---|---|---|
            | UI | Streamlit | Research workspace and dossier dashboard |
            | API | FastAPI | Run control, polling, and structured responses |
            | Intelligence | Five-stage agent pipeline | Plan, search, extract, compare, synthesize |
            | Knowledge | SQLite + ChromaDB | Persistent records and cross-run retrieval |
            | Research | Tavily | External source discovery and page content |
            | LLM | Groq · Llama 3.3 70B | Structured agent reasoning |
            """
        )
    with principles_col:
        st.markdown(
            """
            <div class="surface">
                <div class="surface-title">Design principles</div>
                <div class="workflow-list">
                    <div class="workflow-item"><span class="workflow-number">01</span>Evidence before conclusions</div>
                    <div class="workflow-item"><span class="workflow-number">02</span>Every conclusion has provenance</div>
                    <div class="workflow-item"><span class="workflow-number">03</span>Failures degrade gracefully</div>
                    <div class="workflow-item"><span class="workflow-number">04</span>Knowledge persists across runs</div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown(
    '<div class="footer-note">Modus AI · Enterprise research intelligence · Structured evidence over unsupported summaries</div>',
    unsafe_allow_html=True,
)
