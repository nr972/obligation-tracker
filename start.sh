#!/usr/bin/env bash
# Contract Obligation Tracker — One-command launch script
# Usage: ./start.sh

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Contract Obligation Tracker${NC}"
echo "=================================="

# Create virtual environment if needed
if [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv .venv
fi

# Activate venv
source .venv/bin/activate

# Install dependencies if needed
if ! python -c "import fastapi" 2>/dev/null; then
    echo -e "${YELLOW}Installing dependencies (first run only)...${NC}"
    pip install -e . --quiet
fi

# Create data directories
mkdir -p data/uploads

# Track child PIDs
API_PID=""
FRONTEND_PID=""

# Cleanup function — kills both services regardless of how shutdown
# was initiated (Ctrl+C, SIGTERM from the /shutdown endpoint, etc.)
cleanup() {
    echo ""
    echo -e "${YELLOW}Shutting down...${NC}"
    for pid in $API_PID $FRONTEND_PID; do
        if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null || true
        fi
    done
    # Wait briefly for children to exit
    wait 2>/dev/null || true
    echo -e "${GREEN}Stopped.${NC}"
    exit 0
}
trap cleanup INT TERM

# Start API server in background
echo -e "${GREEN}Starting API server on port 8000...${NC}"
uvicorn ot_app.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

# Wait for API to be ready
echo "Waiting for API..."
for i in $(seq 1 30); do
    if curl -s http://localhost:8000/api/v1/health > /dev/null 2>&1; then
        echo -e "${GREEN}API is ready.${NC}"
        break
    fi
    sleep 1
done

# Open browser (macOS/Linux)
if command -v open &> /dev/null; then
    open http://localhost:8501
elif command -v xdg-open &> /dev/null; then
    xdg-open http://localhost:8501
fi

# Start Streamlit (foreground)
echo -e "${GREEN}Starting dashboard on port 8501...${NC}"
echo ""
echo "  Dashboard: http://localhost:8501"
echo "  API docs:  http://localhost:8000/docs"
echo ""
echo "Press Ctrl+C to stop, or use the Shut Down button in the app."
echo ""

streamlit run ot_frontend/app.py --server.port 8501 --server.headless true &
FRONTEND_PID=$!

# Wait for either child to exit — when the shutdown endpoint fires
# SIGTERM, the trap runs cleanup for both.
wait $API_PID $FRONTEND_PID 2>/dev/null || true
cleanup
