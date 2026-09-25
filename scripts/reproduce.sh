#!/usr/bin/env bash
# reproduce.sh — one-shot reproduction for judges.
# Usage: bash scripts/reproduce.sh
# Output: ./evidence.txt (token table + tx hashes) and frontend/public/runs/two_runs_*.json.

set -euo pipefail
cd "$(dirname "$0")/.."
ROOT="$PWD"

echo "==> [1/5] Installing Python deps (agent + backend)"
python -m pip install -e agent[dev] -e backend[dev] >/dev/null

echo "==> [2/5] Installing frontend deps"
(cd frontend && npm install --no-audit --no-fund --loglevel=error)

echo "==> [3/5] Booting backend on :8000"
PYTHONPATH="$ROOT" python -m uvicorn backend.app.main:app \
    --host 127.0.0.1 --port 8000 --log-level warning &
BACKEND_PID=$!
cleanup() { kill "$BACKEND_PID" "$FRONTEND_PID" 2>/dev/null || true; }
trap cleanup EXIT
sleep 5
curl -sf http://127.0.0.1:8000/api/health >/dev/null

echo "==> [4/5] Booting frontend on :5173"
(cd frontend && npx vite --host 127.0.0.1 --port 5173) &
FRONTEND_PID=$!
sleep 6
curl -sf -o /dev/null http://127.0.0.1:5173/

echo "==> [5/5] Running two-run controlled experiment"
PYTHONPATH="$ROOT" python scripts/two_runs_demo.py

echo "==> Capturing token table + latest mint/revoke hashes"
{
    echo "=== /api/state/tokens ==="
    curl -s http://127.0.0.1:8000/api/state/tokens
    echo ""
    echo "=== latest two runs ==="
    ls -1 frontend/public/runs/two_runs_*.json | tail -1 | xargs -I {} cat {}
    echo ""
} > "$ROOT/evidence.txt"

echo ""
echo "All done. Output: $ROOT/evidence.txt"
echo "Open http://localhost:5173/ in your browser, then Ctrl-C here."
sleep 999999