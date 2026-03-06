#!/usr/bin/env bash
# Railway startup script — runs API and Streamlit in a single container

set -e

mkdir -p data/uploads

# Start API in background
uvicorn ot_app.main:app --host 0.0.0.0 --port 8000 &

# Wait for API
sleep 3

# Start Streamlit in foreground
exec streamlit run ot_frontend/app.py \
    --server.port 8501 \
    --server.headless true \
    --server.address 0.0.0.0
