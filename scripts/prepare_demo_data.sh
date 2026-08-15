#!/usr/bin/env bash
set -euo pipefail

DEMO_DIR="${1:-demo_data}"

if [[ -e "$DEMO_DIR" ]]; then
  BACKUP_DIR="${DEMO_DIR}.backup-$(date +%Y%m%d-%H%M%S)"
  mv "$DEMO_DIR" "$BACKUP_DIR"
  printf 'Existing demo data moved to %s\n' "$BACKUP_DIR"
fi

mkdir -p "$DEMO_DIR"
printf 'Fresh demo data directory ready: %s\n' "$DEMO_DIR"
printf '\nStart the backend with:\n  DATA_DIR=%s uvicorn backend.main:app --reload --port 8000\n' "$DEMO_DIR"
printf '\nStart the frontend in a second terminal with:\n  BACKEND_URL=http://localhost:8000 streamlit run frontend/app.py\n'
