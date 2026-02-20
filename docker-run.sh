#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────────────────────
# docker-run.sh — Build and launch MediaRenamer (browser GUI via noVNC)
#
# Usage:
#   ./docker-run.sh                        # build if needed + launch GUI
#   ./docker-run.sh build                  # force rebuild
#   ./docker-run.sh cli --help             # CLI mode (no display needed)
#   MEDIA_DIR=/srv/movies ./docker-run.sh  # custom media directory
#   TMDB_API_KEY=xxx ./docker-run.sh       # pass key as env var
# ─────────────────────────────────────────────────────────────────────────────
set -euo pipefail

IMAGE="mediarenamer:latest"
CONTAINER="mediarenamer"
SETTINGS_DIR="${HOME}/.mediarenamer"
MEDIA_DIR="${MEDIA_DIR:-${HOME}/Media}"
NOVNC_PORT="${NOVNC_PORT:-6080}"

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[0;33m'; RED='\033[0;31m'; NC='\033[0m'
info()  { echo -e "${CYAN}[mediarenamer]${NC} $*"; }
ok()    { echo -e "${GREEN}[ok]${NC} $*"; }
warn()  { echo -e "${YELLOW}[warn]${NC} $*"; }
error() { echo -e "${RED}[error]${NC} $*"; exit 1; }

# Check Docker
if ! docker info &>/dev/null; then
    error "Docker is not running. Start Docker Desktop and try again."
fi

# Force rebuild
if [[ "${1:-}" == "build" ]]; then
    info "Building image..."
    docker build --no-cache -t "${IMAGE}" "$(dirname "$0")"
    ok "Image built."; exit 0
fi

# CLI passthrough
if [[ "${1:-}" == "cli" ]]; then
    shift
    docker run --rm -it \
        -e TMDB_API_KEY="${TMDB_API_KEY:-}" \
        -v "${SETTINGS_DIR}:/root/.mediarenamer" \
        -v "${MEDIA_DIR}:/media" \
        "${IMAGE}" cli "$@"
    exit 0
fi

# Build image if not present
if ! docker image inspect "${IMAGE}" &>/dev/null; then
    info "Building image (first run, ~3 minutes)..."
    docker build -t "${IMAGE}" "$(dirname "$0")"
    ok "Image built."
fi

# Remove stale container
docker rm -f "${CONTAINER}" &>/dev/null || true

mkdir -p "${SETTINGS_DIR}"
mkdir -p "${MEDIA_DIR}"

info "Starting MediaRenamer..."
docker run -d \
    --name "${CONTAINER}" \
    --rm \
    -p "${NOVNC_PORT}:6080" \
    -e TMDB_API_KEY="${TMDB_API_KEY:-}" \
    -e TVDB_API_KEY="${TVDB_API_KEY:-}" \
    -e OPENSUBTITLES_API_KEY="${OPENSUBTITLES_API_KEY:-}" \
    -e XVFB_RESOLUTION="${XVFB_RESOLUTION:-1280x800x24}" \
    -v "${SETTINGS_DIR}:/root/.mediarenamer" \
    -v "${MEDIA_DIR}:/media" \
    --shm-size=256m \
    "${IMAGE}"

# Wait for noVNC to be ready
info "Waiting for noVNC to start..."
for i in $(seq 1 20); do
    if docker exec "${CONTAINER}" sh -c "ls /tmp/novnc.log 2>/dev/null && grep -q 'handler' /tmp/novnc.log 2>/dev/null || pgrep websockify" &>/dev/null 2>&1; then
        break
    fi
    sleep 0.5
done
sleep 1

echo ""
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}  MediaRenamer is running!${NC}"
echo ""
echo -e "  Browser GUI:  ${CYAN}http://localhost:${NOVNC_PORT}/vnc.html${NC}"
echo -e "  Media files:  ${MEDIA_DIR} → /media inside container"
echo ""
echo -e "  To stop:      ${YELLOW}docker stop ${CONTAINER}${NC}"
echo -e "  To view logs: ${YELLOW}docker logs ${CONTAINER}${NC}"
echo -e "${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"

# Try to open the browser automatically
URL="http://localhost:${NOVNC_PORT}/vnc.html"
case "$(uname -s)" in
    Darwin) sleep 1 && open "$URL" & ;;
    Linux)  sleep 1 && (xdg-open "$URL" &>/dev/null &) & ;;
esac
