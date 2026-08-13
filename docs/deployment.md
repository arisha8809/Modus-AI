# Deployment (free hosting)

Goal: an evaluator should be able to open a link and use the app directly, without any local
setup, while still satisfying the challenge's "free/open-source/free-tier only" and "data must
persist" rules.

## Why not Vercel

Vercel runs on serverless functions with an ephemeral filesystem — files written during a
request (like our SQLite/Chroma data) do not survive between invocations. That directly
conflicts with the brief's requirement that "refreshing or restarting the application must not
simply destroy all intelligence." Vercel is also not designed for long-running Streamlit
processes. So the backend and frontend are split across two services that are actually suited to
this workload, both free.

## Backend — Render (free tier)

1. Push this repo to GitHub (already done: `arisha8809/Modus-AI`).
2. Create a new **Web Service** on [render.com](https://render.com), connect the GitHub repo.
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
5. Add environment variables `GROQ_API_KEY` (from console.groq.com) and `TAVILY_API_KEY`
   (from tavily.com) in Render's dashboard — never commit these to the repo.
6. Attach a **persistent disk** mounted at `/opt/render/project/src/data` (Render's free tier
   supports a small persistent disk) so SQLite/Chroma survive restarts and redeploys. Set the
   `DATA_DIR` environment variable to match.

**Cold starts:** Render's free tier sleeps a service after ~15 minutes of inactivity; the first
request after that takes up to ~30-50 seconds to wake up. For a live demo, ping
`GET /health` a minute or two beforehand so the service is warm when the evaluator interacts
with it.

## Frontend — Streamlit Community Cloud (free)

1. Go to [share.streamlit.io](https://share.streamlit.io), connect the same GitHub repo.
2. App file: `frontend/app.py`
3. In the app's secrets, set `BACKEND_URL` to the Render backend's public URL.
4. Deploys automatically on every push to `main`.

## Result

- Evaluator opens the Streamlit Cloud URL → sees the working app immediately, no setup.
- Full source code is public on GitHub for review alongside it.
- Data persists across both services' restarts via Render's persistent disk.
- Total cost: $0, no credit card required anywhere in the stack.
