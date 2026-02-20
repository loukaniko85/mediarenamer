#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer entrypoint
#
# Starts:  Xvfb  →  x11vnc  →  noVNC  →  FastAPI API  →  Qt GUI
#
# Access:
#   GUI:      http://localhost:6080/vnc.html
#   REST API: http://localhost:8000/docs
# ─────────────────────────────────────────────────────────────────────────────
set -e

DISPLAY_NUM=1
DISPLAY=":${DISPLAY_NUM}"
RESOLUTION="${XVFB_RESOLUTION:-1440x900x24}"
VNC_PORT=5901
NOVNC_PORT=6080
API_PORT="${API_PORT:-8000}"
API_HOST="${API_HOST:-0.0.0.0}"

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MediaRenamer"
echo "  GUI:  http://localhost:${NOVNC_PORT}/vnc.html"
echo "  API:  http://localhost:${API_PORT}/docs"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. CLI passthrough ────────────────────────────────────────────────────────
if [ "$1" = "cli" ]; then
    shift
    exec python3 /app/cli.py "$@"
fi

# ── 2. API-only mode (no GUI) ─────────────────────────────────────────────────
if [ "$1" = "api" ]; then
    echo "[api] Starting FastAPI only on ${API_HOST}:${API_PORT}..."
    exec uvicorn api.app:app --host "${API_HOST}" --port "${API_PORT}" --app-dir /app
fi

# ── 3. Start Xvfb ────────────────────────────────────────────────────────────
echo "[1/5] Xvfb on ${DISPLAY} (${RESOLUTION})..."
Xvfb "${DISPLAY}" -screen 0 "${RESOLUTION}" -ac +extension GLX +render -noreset &
XVFB_PID=$!

for i in $(seq 1 20); do
    [ -f "/tmp/.X${DISPLAY_NUM}-lock" ] && echo "      Xvfb ready." && break
    sleep 0.3
done
export DISPLAY="${DISPLAY}"
command -v xsetroot &>/dev/null && xsetroot -solid "#0A0C12" 2>/dev/null || true

# ── 4. Start x11vnc ──────────────────────────────────────────────────────────
echo "[2/5] x11vnc on VNC port ${VNC_PORT}..."
x11vnc -display "${DISPLAY}" -forever -shared -nopw \
       -rfbport "${VNC_PORT}" -bg -quiet \
       -logfile /tmp/x11vnc.log 2>/dev/null || true
sleep 0.5

# ── 5. Start noVNC ───────────────────────────────────────────────────────────
echo "[3/5] noVNC on port ${NOVNC_PORT}..."
NOVNC_PATH=""
for p in /usr/share/novnc /usr/lib/novnc /opt/novnc; do
    [ -d "$p" ] && NOVNC_PATH="$p" && break
done
[ -z "$NOVNC_PATH" ] && echo "ERROR: noVNC not found" && exit 1

websockify --web "${NOVNC_PATH}" "${NOVNC_PORT}" "localhost:${VNC_PORT}" \
    &>/tmp/novnc.log &
sleep 0.5

# ── 6. Start FastAPI ─────────────────────────────────────────────────────────
echo "[4/5] FastAPI on ${API_HOST}:${API_PORT}..."
cd /app
uvicorn api.app:app \
    --host "${API_HOST}" \
    --port "${API_PORT}" \
    --log-level warning \
    &>/tmp/api.log &
API_PID=$!
sleep 1
echo "      API ready."

# ── 7. Launch GUI ─────────────────────────────────────────────────────────────
echo "[5/5] Launching GUI..."
echo ""
echo "  ┌──────────────────────────────────────────────────┐"
echo "  │  GUI:  http://localhost:${NOVNC_PORT}/vnc.html         │"
echo "  │  API:  http://localhost:${API_PORT}/docs              │"
echo "  │  Media files: /media                             │"
echo "  └──────────────────────────────────────────────────┘"
echo ""

python3 /app/main.py
EXIT_CODE=$?
kill $XVFB_PID $API_PID 2>/dev/null || true
exit $EXIT_CODE
