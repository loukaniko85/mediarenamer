#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer entrypoint — starts Xvfb → x11vnc → noVNC → app
#
# GUI accessible at: http://localhost:6080/vnc.html
# ─────────────────────────────────────────────────────────────────────────────
set -e

DISPLAY_NUM=1
DISPLAY=":${DISPLAY_NUM}"
RESOLUTION="${XVFB_RESOLUTION:-1280x800x24}"
VNC_PORT=5901
NOVNC_PORT=6080

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  MediaRenamer — Browser GUI"
echo "  Open: http://localhost:${NOVNC_PORT}/vnc.html"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

# ── 1. Start Xvfb virtual display ────────────────────────────────────────────
echo "[1/4] Starting Xvfb on ${DISPLAY} (${RESOLUTION})..."
Xvfb "${DISPLAY}" -screen 0 "${RESOLUTION}" -ac +extension GLX +render -noreset &
XVFB_PID=$!

# Wait for Xvfb to be ready (poll /tmp/.X${DISPLAY_NUM}-lock)
for i in $(seq 1 20); do
    if [ -f "/tmp/.X${DISPLAY_NUM}-lock" ]; then
        echo "    Xvfb ready."
        break
    fi
    sleep 0.3
done

export DISPLAY="${DISPLAY}"

# ── 2. Set a solid background colour (optional — hides Xvfb grey grid) ───────
if command -v xsetroot &>/dev/null; then
    xsetroot -solid "#0A0C12" 2>/dev/null || true
fi

# ── 3. Start x11vnc (VNC server on top of Xvfb) ─────────────────────────────
echo "[2/4] Starting x11vnc on port ${VNC_PORT}..."
x11vnc \
    -display "${DISPLAY}" \
    -forever \
    -shared \
    -nopw \
    -rfbport "${VNC_PORT}" \
    -bg \
    -quiet \
    -logfile /tmp/x11vnc.log \
    2>/dev/null || {
        echo "x11vnc failed — check /tmp/x11vnc.log"
    }
sleep 0.5

# ── 4. Start noVNC (WebSocket bridge for browser access) ─────────────────────
echo "[3/4] Starting noVNC on port ${NOVNC_PORT}..."
NOVNC_PATH=""
for p in /usr/share/novnc /usr/lib/novnc /opt/novnc; do
    if [ -d "$p" ]; then
        NOVNC_PATH="$p"
        break
    fi
done

if [ -z "$NOVNC_PATH" ]; then
    echo "ERROR: noVNC not found. Install it with: apt-get install novnc"
    exit 1
fi

websockify \
    --web "${NOVNC_PATH}" \
    "${NOVNC_PORT}" \
    "localhost:${VNC_PORT}" \
    &>/tmp/novnc.log &
NOVNC_PID=$!
sleep 0.5

echo "[4/4] Launching MediaRenamer..."
echo ""
echo "  ┌─────────────────────────────────────────────┐"
echo "  │  Open your browser and navigate to:         │"
echo "  │  http://localhost:${NOVNC_PORT}/vnc.html         │"
echo "  │                                             │"
echo "  │  Media files available at: /media           │"
echo "  └─────────────────────────────────────────────┘"
echo ""

# ── 5. Launch the app (CLI passthrough or GUI) ────────────────────────────────
if [ "$1" = "cli" ]; then
    shift
    exec python3 /app/cli.py "$@"
else
    # GUI — keep running until the app exits, then clean up
    python3 /app/main.py "$@"
    EXIT_CODE=$?
    kill $XVFB_PID $NOVNC_PID 2>/dev/null || true
    exit $EXIT_CODE
fi
