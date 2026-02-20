#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# docker-run.sh — Launch MediaRenamer GUI from Docker on Linux, macOS, Windows
#
# Usage:
#   ./docker-run.sh                        # GUI (default)
#   ./docker-run.sh cli --help             # CLI mode
#   ./docker-run.sh cli rename /media/...  # CLI rename
#   MEDIA_DIR=/srv/movies ./docker-run.sh  # custom media directory
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

IMAGE="mediarenamer:latest"
CONTAINER_NAME="mediarenamer"
SETTINGS_DIR="${HOME}/.mediarenamer"
MEDIA_DIR="${MEDIA_DIR:-${HOME}/Media}"

# ── Colour helpers ────────────────────────────────────────────────────────────
RED='\033[0;31m'; YELLOW='\033[0;33m'; GREEN='\033[0;32m'; CYAN='\033[0;36m'; NC='\033[0m'
info()  { echo -e "${CYAN}[mediarenamer]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warning]${NC} $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }
ok()    { echo -e "${GREEN}[ok]${NC} $*"; }

# ── Detect OS ─────────────────────────────────────────────────────────────────
OS="unknown"
case "$(uname -s)" in
  Linux*)  OS="linux"  ;;
  Darwin*) OS="macos"  ;;
  MINGW*|MSYS*|CYGWIN*) OS="windows" ;;
esac
info "Host OS: ${OS}"

# ── Check Docker is running ───────────────────────────────────────────────────
if ! docker info &>/dev/null; then
  error "Docker daemon is not running. Start Docker and try again."
fi

# ── Build image if it doesn't exist ──────────────────────────────────────────
if ! docker image inspect "${IMAGE}" &>/dev/null; then
  info "Image '${IMAGE}' not found — building now (this takes ~2 minutes the first time)…"
  docker build -t "${IMAGE}" "$(dirname "$0")"
  ok "Image built."
fi

# ── Persistent settings directory ─────────────────────────────────────────────
mkdir -p "${SETTINGS_DIR}"
info "Settings dir: ${SETTINGS_DIR}"

# ── Media directory ───────────────────────────────────────────────────────────
if [ ! -d "${MEDIA_DIR}" ]; then
  warn "MEDIA_DIR '${MEDIA_DIR}' does not exist — creating it."
  mkdir -p "${MEDIA_DIR}"
fi
info "Media dir: ${MEDIA_DIR}"

# ── Remove any stopped container with the same name ──────────────────────────
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
  docker rm -f "${CONTAINER_NAME}" &>/dev/null || true
fi

# ── Common docker run flags ───────────────────────────────────────────────────
DOCKER_ARGS=(
  --rm
  --name "${CONTAINER_NAME}"
  -v "${SETTINGS_DIR}:/root/.mediarenamer"
  -v "${MEDIA_DIR}:/media"
  -e TMDB_API_KEY="${TMDB_API_KEY:-}"
  -e TVDB_API_KEY="${TVDB_API_KEY:-}"
  -e OPENSUBTITLES_API_KEY="${OPENSUBTITLES_API_KEY:-}"
  --ipc host
)

# ── CLI mode: pass args straight through ─────────────────────────────────────
if [[ "${1:-}" == "cli" ]]; then
  shift
  info "Running CLI: python3 cli.py $*"
  exec docker run -it "${DOCKER_ARGS[@]}" "${IMAGE}" python3 cli.py "$@"
fi

# ── GUI mode: set up X11 forwarding per OS ───────────────────────────────────
case "${OS}" in

  # ────────────────────────────────────────────────────────────────────────────
  linux)
    # Validate DISPLAY is set
    if [ -z "${DISPLAY:-}" ]; then
      error "DISPLAY is not set. Are you running in a desktop session?"
    fi

    # Grant the container permission to open windows
    if command -v xhost &>/dev/null; then
      xhost +local:docker &>/dev/null && ok "xhost: granted access to local:docker"
    else
      warn "xhost not found — if the window fails to open, install x11-xserver-utils"
    fi

    DOCKER_ARGS+=(
      -e DISPLAY="${DISPLAY}"
      -v /tmp/.X11-unix:/tmp/.X11-unix:ro
    )

    info "Launching GUI (Linux/X11)…"
    docker run -it "${DOCKER_ARGS[@]}" "${IMAGE}"

    # Revoke xhost access when done
    if command -v xhost &>/dev/null; then
      xhost -local:docker &>/dev/null || true
    fi
    ;;

  # ────────────────────────────────────────────────────────────────────────────
  macos)
    # Requires XQuartz — https://www.xquartz.org/
    if ! command -v xquartz &>/dev/null && ! [ -d /Applications/Utilities/XQuartz.app ]; then
      error "XQuartz is not installed.\nInstall it from https://www.xquartz.org/ then re-run this script."
    fi

    # Make sure XQuartz is running
    if ! pgrep -x Xquartz &>/dev/null && ! pgrep -f "X11.bin" &>/dev/null; then
      info "Starting XQuartz…"
      open -a XQuartz
      sleep 3  # give it time to initialise
    fi

    # Allow connections from localhost
    if command -v xhost &>/dev/null; then
      xhost +localhost &>/dev/null && ok "xhost: granted localhost access"
    fi

    # Get the host's IP on the loopback interface that the container can reach
    HOST_IP=$(ifconfig lo0 | grep 'inet ' | awk '{print $2}')
    if [ -z "${HOST_IP}" ]; then
      HOST_IP="host.docker.internal"  # Docker Desktop fallback
    fi

    DOCKER_ARGS+=(
      -e DISPLAY="${HOST_IP}:0"
    )

    info "Launching GUI (macOS → XQuartz at ${HOST_IP}:0)…"
    echo ""
    echo "  Tip: In XQuartz Preferences → Security, enable"
    echo "       'Allow connections from network clients'"
    echo "  Then restart XQuartz and re-run this script."
    echo ""
    docker run -it "${DOCKER_ARGS[@]}" "${IMAGE}"
    ;;

  # ────────────────────────────────────────────────────────────────────────────
  windows)
    # Option A: WSL2 with WSLg (Windows 11 / recent Win10) — DISPLAY is set automatically
    # Option B: VcXsrv / Xming on the host — user must set DISPLAY manually

    DISPLAY_VAR="${DISPLAY:-}"

    if [ -z "${DISPLAY_VAR}" ]; then
      # Try to auto-detect the Windows host IP for VcXsrv
      DISPLAY_VAR="$(grep -m1 nameserver /etc/resolv.conf | awk '{print $2}'):0.0"
      warn "DISPLAY not set — guessing ${DISPLAY_VAR} (VcXsrv/Xming default)."
      warn "If the window doesn't appear:"
      warn "  1. Install VcXsrv from https://sourceforge.net/projects/vcxsrv/"
      warn "  2. Launch XLaunch with 'Disable access control' checked"
      warn "  3. Set DISPLAY=<your-host-ip>:0.0 then re-run this script"
    else
      ok "Using DISPLAY=${DISPLAY_VAR}"
    fi

    DOCKER_ARGS+=(
      -e DISPLAY="${DISPLAY_VAR}"
    )

    info "Launching GUI (Windows → VcXsrv/WSLg at ${DISPLAY_VAR})…"
    docker run -it "${DOCKER_ARGS[@]}" "${IMAGE}"
    ;;

  *)
    error "Unsupported OS: $(uname -s). Run the container manually and set DISPLAY."
    ;;
esac
