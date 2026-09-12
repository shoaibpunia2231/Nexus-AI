#!/bin/bash
# start.sh — Run the full Nexus AI stack locally
# Usage: bash start.sh

set -e

echo ""
echo "======================================"
echo "   Nexus AI — Local Startup Script   "
echo "======================================"
echo ""

# ── Step 1: Check Python ─────────────────────────────────────
if ! command -v python3 &> /dev/null; then
  echo "[ERROR] Python 3 is not installed. Please install Python 3.9+."
  exit 1
fi
echo "[OK] Python: $(python3 --version)"

# ── Step 2: Install Python deps ──────────────────────────────
echo ""
echo "[SETUP] Installing Python dependencies..."
pip install -r requirements.txt --quiet

# ── Step 3: Train model if not already trained ───────────────
if [ ! -f "ml/models/model.pkl" ]; then
  echo ""
  echo "[TRAIN] model.pkl not found — training the model now..."
  cd ml && python3 train_model.py && cd ..
  echo "[TRAIN] Model trained and saved."
else
  echo "[OK] model.pkl already exists. Skipping training."
fi

# ── Step 4: Start backend in background ─────────────────────
echo ""
echo "[API] Starting FastAPI backend on http://localhost:8000 ..."
cd backend
uvicorn main:app --reload --port 8000 &
BACKEND_PID=$!
cd ..
echo "[API] Backend started (PID $BACKEND_PID)"
sleep 2

# ── Step 5: Check Node.js ────────────────────────────────────
if ! command -v node &> /dev/null; then
  echo "[WARN] Node.js not found. Please install Node 18+ to run the frontend."
  echo "       Backend API is available at http://localhost:8000"
  wait $BACKEND_PID
  exit 0
fi
echo "[OK] Node: $(node --version)"

# ── Step 6: Install & start frontend ─────────────────────────
echo ""
echo "[FRONTEND] Installing npm packages..."
cd frontend
npm install --silent
echo "[FRONTEND] Starting React app on http://localhost:5173 ..."
npm run dev &
FRONTEND_PID=$!
cd ..

echo ""
echo "======================================"
echo "  All services running!"
echo "  Frontend:  http://localhost:5173"
echo "  Backend:   http://localhost:8000"
echo "  API Docs:  http://localhost:8000/docs"
echo "======================================"
echo "  Press Ctrl+C to stop all services."
echo ""

# Wait for both processes
wait $BACKEND_PID $FRONTEND_PID
