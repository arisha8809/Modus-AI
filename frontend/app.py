"""
Enterprise AI Research Agent -- Streamlit UI.

Talks to the FastAPI backend over HTTP (set BACKEND_URL in .env or
Streamlit secrets when deployed). Three tabs:

  1. New Research  -- submit any question, watch the pipeline run live.
     This is the tab used for the "surprise record" live demo.
  2. Knowledge Base -- browse every past research run, semantically search
     across all findings ever collected.
  3. About          -- architecture explanation for reviewers.
"""

import os
import time
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()  # reads .env for BACKEND_URL etc. when running locally

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

st.set_page_config(page_title="Enterprise AI Research Agent", layout="wide")
st.title("🔎 Enterprise AI Research Agent")
st.caption("Structured, traceable, multi-agent enterprise research at scale — powered by Groq (Llama 3.3 70B).")

tab_new, tab_kb, tab_about = st.tabs(["New Research", "Knowledge Base", "About"])


# ---------------------------------------------------------------- New Research
with tab_new:
    st.subheader("Ask a research question")
    st.write(
        "Ask about any industry or topic — there's no fixed domain. "
        "A classifier agent detects the domain and plans the research automatically."
    )
    question = st.text_input(
        "Research question",
        placeholder="e.g. How is AI transforming retail operations?",
    )
    submit = st.button("Run research", type="primary")

    if submit and question.strip():
        resp = requests.post(f"{BACKEND_URL}/research", json={"question": question.strip()})
        if resp.status_code != 200:
            st.error(f"Failed to start research: {resp.text}")
        else:
            topic_id = resp.json()["id"]
            st.session_state["active_topic_id"] = topic_id

    topic_id = st.session_state.get("active_topic_id")
    if topic_id:
        status_box = st.empty()
        events_box = st.container()
        results_box = st.container()

        # Poll until the pipeline finishes, showing live stage-by-stage progress.
        placeholder_events = []
        for _ in range(180):  # ~6 minutes max poll window
            detail = requests.get(f"{BACKEND_URL}/research/{topic_id}").json()
            status_box.info(f"**Status:** {detail['status']}  |  **Domain:** {detail.get('domain') or 'detecting...'}")

            with events_box:
                st.markdown("**Pipeline progress**")
                for e in detail["events"]:
                    st.text(f"[{e['stage']}] {e['message']}")

            if detail["status"] in ("done", "failed"):
                if detail["status"] == "done":
                    with results_box:
                        st.markdown("### Conclusions")
                        for c in detail["conclusions"]:
                            st.markdown(f"**• {c['text']}**")
                            with st.expander(f"Evidence ({len(c['findings'])} finding(s))"):
                                for f in c["findings"]:
                                    st.write(f"- *{f['claim']}* — `{f['classification']}` — [{f['source_url']}]({f['source_url']})")

                        if detail["contradictions"]:
                            st.markdown("### ⚠️ Contradictions detected")
                            st.caption("Sources that disagree with each other — surfaced explicitly, not just logged.")
                            for c in detail["contradictions"]:
                                st.warning(
                                    f"**{c['explanation']}**\n\n"
                                    f"- *{c['finding_a']['claim']}* — [{c['finding_a']['source_url']}]({c['finding_a']['source_url']})\n"
                                    f"- *{c['finding_b']['claim']}* — [{c['finding_b']['source_url']}]({c['finding_b']['source_url']})"
                                )
                else:
                    st.error("Pipeline failed. Check the event log above for the error.")
                break

            events_box.empty()
            time.sleep(2)


# ------------------------------------------------------------------- Knowledge Base
with tab_kb:
    st.subheader("Past research runs")
    topics = requests.get(f"{BACKEND_URL}/research").json()
    if not topics:
        st.write("No research runs yet — submit one in the 'New Research' tab.")
    for t in topics:
        with st.expander(f"[{t['status']}] {t['question']}  —  domain: {t.get('domain') or '—'}"):
            detail = requests.get(f"{BACKEND_URL}/research/{t['id']}").json()
            for c in detail["conclusions"]:
                st.markdown(f"- {c['text']}")

    st.divider()
    st.subheader("Semantic search across all findings")
    kb_query = st.text_input("Search the knowledge base", key="kb_search")
    if kb_query:
        results = requests.get(f"{BACKEND_URL}/knowledge-base/search", params={"q": kb_query}).json()
        for hit in results["results"]:
            st.write(f"- {hit['text']}  \n  *source: {hit['metadata'].get('source_url')}*")


# ------------------------------------------------------------------------- About
with tab_about:
    st.markdown("""
### Architecture

**UI layer** — this Streamlit app.
**API layer** — FastAPI (`backend/main.py`), exposes `/research` endpoints.
**AI Intelligence layer** — a 5-agent pipeline (`backend/agents/`):
Classifier → Search → Extraction → Evidence → Synthesis.
**Data & Knowledge layer** — SQLite (structured, persistent) + ChromaDB
(vector store for semantic search), both under `./data`, both survive restarts.
**External Research** — DuckDuckGo web search + page fetching, both free,
no API key required.

**LLM provider** — Groq free-tier API, serving the open-weight Llama 3.3 70B
model. All LLM calls go through one file (`backend/agents/llm_client.py`) so
swapping providers is a one-line change if Groq's free tier ever becomes
unavailable.

See `README.md` and `docs/architecture.md` in the repository for full detail.
""")
