#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer AppImage builder
#
# Usage:
#   ./build_appimage.sh [--arch aarch64]
#
# Requirements (auto-handled on missing):
#   python3, python3-venv, python3-pip, wget
#   appimagetool — downloaded automatically if not on PATH
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_NAME="MediaRenamer"
APP_ID="net.mediarenamer.app"
APP_VERSION="1.1"
ARCH="${1:-x86_64}"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══════════════════════════════════════════════════════════"
echo "  Building $APP_NAME $APP_VERSION AppImage ($ARCH)"
echo "═══════════════════════════════════════════════════════════"

# ── 1. Workspace ──────────────────────────────────────────────────────────────
WORK_DIR="$(mktemp -d)"
APP_DIR="${WORK_DIR}/${APP_NAME}.AppDir"

mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/share/applications"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/16x16/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/24x24/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/32x32/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/48x48/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/64x64/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/128x128/apps"
mkdir -p "${APP_DIR}/usr/share/icons/hicolor/256x256/apps"

# ── 2. Copy app sources ───────────────────────────────────────────────────────
echo "[1/6] Copying application sources..."
rsync -a --exclude='*.pyc' --exclude='__pycache__' \
    --exclude='.git' --exclude='*.AppDir' \
    --exclude='build_appimage*.sh' \
    --exclude='*.AppImage' \
    "${SCRIPT_DIR}/" "${APP_DIR}/usr/lib/mediarenamer/"

# ── 3. Create virtualenv and install dependencies ─────────────────────────────
# Using a virtualenv rather than pip --target so that compiled extensions
# (PyQt6.sip, PyQt6 .so files) are installed into a proper site-packages
# layout that Python can actually find at runtime.
echo "[2/6] Creating virtualenv and installing dependencies..."

VENV_DIR="${APP_DIR}/usr/venv"
python3 -m venv "${VENV_DIR}"

# Upgrade pip inside venv quietly
"${VENV_DIR}/bin/pip" install --upgrade pip --quiet

# Install all runtime dependencies
"${VENV_DIR}/bin/pip" install \
    PyQt6 \
    requests \
    pymediainfo \
    mutagen \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    --quiet

echo "      ✓ virtualenv ready"
PYQT_VER=$("${VENV_DIR}/bin/python3" -c \
    'from PyQt6.QtCore import QT_VERSION_STR; print(QT_VERSION_STR)' 2>/dev/null || echo 'unknown')
echo "      ✓ Qt version: ${PYQT_VER}"

# Smoke-test: make sure PyQt6.sip imports cleanly
"${VENV_DIR}/bin/python3" -c "import PyQt6.sip; import PyQt6.QtWidgets" 2>/dev/null \
    && echo "      ✓ PyQt6 import smoke-test passed" \
    || { echo "ERROR: PyQt6 smoke-test failed"; exit 1; }

# ── 4. .desktop file ─────────────────────────────────────────────────────────
echo "[3/6] Writing .desktop entry..."
cat > "${APP_DIR}/mediarenamer.desktop" << DESKTOPEOF
[Desktop Entry]
Name=MediaRenamer
Comment=The open-source FileBot alternative — rename and organise your media
Exec=mediarenamer %F
Icon=mediarenamer
Type=Application
Categories=AudioVideo;Video;
MimeType=video/mp4;video/x-matroska;video/avi;video/quicktime;video/x-msvideo;
Keywords=rename;media;movies;tvshows;anime;organise;
Terminal=false
StartupWMClass=MediaRenamer
X-AppImage-Name=MediaRenamer
X-AppImage-Version=${APP_VERSION}
X-AppImage-Arch=${ARCH}
DESKTOPEOF
cp "${APP_DIR}/mediarenamer.desktop" "${APP_DIR}/usr/share/applications/mediarenamer.desktop"

# ── 5. Icons ──────────────────────────────────────────────────────────────────
echo "[4/6] Installing icons..."
for SIZE in 16 24 32 48 64 128 256; do
    SRC="${SCRIPT_DIR}/assets/mediarenamer_${SIZE}.png"
    DST="${APP_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/mediarenamer.png"
    if [ -f "${SRC}" ]; then
        cp "${SRC}" "${DST}"
        echo "  ✓ ${SIZE}×${SIZE}"
    else
        echo "  ⚠ assets/mediarenamer_${SIZE}.png not found — skipping"
    fi
done

# Root icon — required by appimagetool for taskbar display
if [ -f "${SCRIPT_DIR}/assets/mediarenamer_256.png" ]; then
    cp "${SCRIPT_DIR}/assets/mediarenamer_256.png" "${APP_DIR}/mediarenamer.png"
    echo "  ✓ Root icon (256px)"
elif [ -f "${SCRIPT_DIR}/assets/mediarenamer.png" ]; then
    cp "${SCRIPT_DIR}/assets/mediarenamer.png" "${APP_DIR}/mediarenamer.png"
    echo "  ✓ Root icon (fallback)"
else
    echo "  ⚠ WARNING: No root icon found"
fi

# ── 6. AppRun launcher ────────────────────────────────────────────────────────
echo "[5/6] Writing AppRun launcher..."
cat > "${APP_DIR}/AppRun" << 'APPRUNEOF'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="$(dirname "${SELF}")"

# Use the bundled virtualenv Python so compiled extensions
# (PyQt6.sip etc.) are in a proper site-packages layout
PYTHON="${HERE}/usr/venv/bin/python3"

# Qt plugins path — use bundled Qt6 plugins from the venv
_PYQT6_DIR="$(ls -d "${HERE}/usr/venv/lib/python3."*/site-packages/PyQt6 2>/dev/null | head -1)"
if [ -d "${_PYQT6_DIR}/Qt6/plugins" ]; then
    export QT_PLUGIN_PATH="${_PYQT6_DIR}/Qt6/plugins"
fi

# Prevent Qt from complaining about missing platform theme
export QT_QPA_PLATFORMTHEME=

# Mark as AppImage so the About dialog shows the right info
export APPIMAGE="${APPIMAGE:-appimage}"

exec "${PYTHON}" "${HERE}/usr/lib/mediarenamer/main.py" "$@"
APPRUNEOF
chmod +x "${APP_DIR}/AppRun"

# ── 7. Ensure appimagetool is available ──────────────────────────────────────
# appimagetool is itself an AppImage. On systems without FUSE (GitHub Actions),
# we extract it with --appimage-extract (no FUSE needed) and run AppRun directly.
echo "[6/6] Building AppImage with appimagetool..."
OUTPUT="${SCRIPT_DIR}/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

_APPIMAGETOOL=""
_TOOL_DIR=""

if command -v appimagetool &>/dev/null && appimagetool --version &>/dev/null 2>&1; then
    _APPIMAGETOOL="appimagetool"
    echo "      Using system appimagetool"
else
    echo "      Downloading appimagetool..."
    _TOOL_DIR="$(mktemp -d)"
    wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
        -O "${_TOOL_DIR}/appimagetool.AppImage"
    chmod +x "${_TOOL_DIR}/appimagetool.AppImage"

    echo "      Extracting (no FUSE required)..."
    cd "${_TOOL_DIR}"
    "${_TOOL_DIR}/appimagetool.AppImage" --appimage-extract >/dev/null 2>&1
    cd "${SCRIPT_DIR}"

    _APPIMAGETOOL="${_TOOL_DIR}/squashfs-root/AppRun"
    if [ ! -x "${_APPIMAGETOOL}" ]; then
        echo "ERROR: appimagetool extraction failed"
        rm -rf "${_TOOL_DIR}" "${WORK_DIR}"
        exit 1
    fi
    echo "      appimagetool ready"
fi

ARCH="${ARCH}" "${_APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT}" 2>&1
BUILD_EXIT=$?

# Cleanup
[ -n "${_TOOL_DIR}" ] && rm -rf "${_TOOL_DIR}"
rm -rf "${WORK_DIR}"

if [ "${BUILD_EXIT}" -ne 0 ]; then
    echo "ERROR: appimagetool exited with code ${BUILD_EXIT}"
    exit "${BUILD_EXIT}"
fi

chmod +x "${OUTPUT}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ AppImage built: ${OUTPUT}"
echo "  Size: $(du -h "${OUTPUT}" | cut -f1)"
echo "  Run:  ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo "═══════════════════════════════════════════════════════════"
