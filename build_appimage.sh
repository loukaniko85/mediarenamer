#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer AppImage builder
#
# Bundles a self-contained Python 3.11 interpreter (from niess/python-appimage)
# so the AppImage runs on any Linux regardless of the system Python version.
#
# Usage:  ./build_appimage.sh
# Needs:  bash, wget, rsync
# ─────────────────────────────────────────────────────────────────────────────
set -e

APP_NAME="MediaRenamer"
APP_VERSION="1.1"
ARCH="x86_64"
PYTHON_VERSION="3.11"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

echo "═══════════════════════════════════════════════════════════"
echo "  Building $APP_NAME $APP_VERSION AppImage"
echo "  Python $PYTHON_VERSION bundled (self-contained)"
echo "═══════════════════════════════════════════════════════════"

WORK_DIR="$(mktemp -d)"
trap 'rm -rf "${WORK_DIR}"' EXIT

# ── 1. Download & extract the Python AppImage ─────────────────────────────────
# niess/python-appimage publishes pre-built, relocatable Python AppImages.
# We extract it (no FUSE needed) and use its Python as our base.
echo "[1/5] Fetching Python ${PYTHON_VERSION} AppImage..."

# Query GitHub API for the latest asset URL for this Python version
PYTHON_ASSET_URL=$(wget -qO- \
    "https://api.github.com/repos/niess/python-appimage/releases/tags/python${PYTHON_VERSION}" \
    | grep '"browser_download_url"' \
    | grep "manylinux.*${ARCH}\.AppImage" \
    | head -1 \
    | sed 's/.*"browser_download_url": *"\([^"]*\)".*/\1/')

if [ -z "${PYTHON_ASSET_URL}" ]; then
    echo "  GitHub API did not return a URL — trying known fallback..."
    # Fallback to a known stable release URL
    PYTHON_ASSET_URL="https://github.com/niess/python-appimage/releases/download/python${PYTHON_VERSION}/python${PYTHON_VERSION}.0-cp311-cp311-manylinux_2_28_x86_64.AppImage"
fi

echo "  URL: ${PYTHON_ASSET_URL}"
wget -q --show-progress "${PYTHON_ASSET_URL}" -O "${WORK_DIR}/python.AppImage" || {
    # If version-specific URL fails, try a different common format
    echo "  Primary URL failed, trying alternate format..."
    wget -q --show-progress \
        "https://github.com/niess/python-appimage/releases/download/python${PYTHON_VERSION}/python${PYTHON_VERSION}-cp311-cp311-manylinux2014_x86_64.AppImage" \
        -O "${WORK_DIR}/python.AppImage"
}

chmod +x "${WORK_DIR}/python.AppImage"

echo "  Extracting Python AppImage (no FUSE required)..."
cd "${WORK_DIR}"
"${WORK_DIR}/python.AppImage" --appimage-extract >/dev/null 2>&1
APP_DIR="${WORK_DIR}/squashfs-root"
cd "${SCRIPT_DIR}"

# Verify the extracted Python works
BUNDLED_PYTHON="${APP_DIR}/usr/bin/python${PYTHON_VERSION}"
if [ ! -f "${BUNDLED_PYTHON}" ]; then
    # Try alternate path
    BUNDLED_PYTHON=$(find "${APP_DIR}" -name "python${PYTHON_VERSION}" -type f | head -1)
fi
if [ ! -f "${BUNDLED_PYTHON}" ]; then
    echo "ERROR: Cannot find python${PYTHON_VERSION} in extracted AppImage"
    ls "${APP_DIR}/usr/bin/"
    exit 1
fi
echo "  Bundled Python: ${BUNDLED_PYTHON}"
echo "  Version: $(PYTHONHOME="${APP_DIR}/usr" "${BUNDLED_PYTHON}" --version)"

# ── 2. Install dependencies into bundled Python ───────────────────────────────
echo "[2/5] Installing dependencies into bundled Python..."

# The bundled Python's pip — set PYTHONHOME so stdlib is found
BUNDLED_PIP="${APP_DIR}/usr/bin/pip${PYTHON_VERSION}"
if [ ! -f "${BUNDLED_PIP}" ]; then
    BUNDLED_PIP="${APP_DIR}/usr/bin/pip3"
fi

PYTHONHOME="${APP_DIR}/usr" "${BUNDLED_PIP}" install --upgrade pip --quiet 2>&1 | tail -2

PYTHONHOME="${APP_DIR}/usr" "${BUNDLED_PIP}" install \
    PyQt6 \
    requests \
    pymediainfo \
    mutagen \
    fastapi \
    "uvicorn[standard]" \
    pydantic \
    --quiet

echo "  ✓ Dependencies installed"

# Quick import check (headless-safe — QtCore only, not QtWidgets)
PYTHONHOME="${APP_DIR}/usr" "${BUNDLED_PYTHON}" \
    -c "import PyQt6.sip; import PyQt6.QtCore; print('  ✓ PyQt6 import OK')"

# ── 3. Copy application files ─────────────────────────────────────────────────
echo "[3/5] Installing application files..."
APP_INSTALL="${APP_DIR}/usr/share/mediarenamer"
mkdir -p "${APP_INSTALL}"

rsync -a \
    --exclude='*.pyc' --exclude='__pycache__' \
    --exclude='.git' --exclude='*.AppImage' \
    --exclude='build_appimage*.sh' \
    --exclude='squashfs-root' \
    "${SCRIPT_DIR}/" "${APP_INSTALL}/"

# ── 4. Desktop entry, icons, AppRun ───────────────────────────────────────────
echo "[4/5] Writing desktop entry, icons, AppRun..."

# Desktop entry (replaces the python-appimage one)
cat > "${APP_DIR}/mediarenamer.desktop" << DESKTOPEOF
[Desktop Entry]
Name=MediaRenamer
Comment=Rename and organise your media files
Exec=mediarenamer %F
Icon=mediarenamer
Type=Application
Categories=AudioVideo;Video;
MimeType=video/mp4;video/x-matroska;video/avi;video/quicktime;video/x-msvideo;
Keywords=rename;media;movies;tvshows;anime;
Terminal=false
StartupWMClass=MediaRenamer
X-AppImage-Name=MediaRenamer
X-AppImage-Version=${APP_VERSION}
DESKTOPEOF

mkdir -p "${APP_DIR}/usr/share/applications"
cp "${APP_DIR}/mediarenamer.desktop" "${APP_DIR}/usr/share/applications/mediarenamer.desktop"

# Icons (all sizes)
for SIZE in 16 24 32 48 64 128 256; do
    SRC="${SCRIPT_DIR}/assets/mediarenamer_${SIZE}.png"
    if [ -f "${SRC}" ]; then
        mkdir -p "${APP_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps"
        cp "${SRC}" "${APP_DIR}/usr/share/icons/hicolor/${SIZE}x${SIZE}/apps/mediarenamer.png"
    fi
done
# Root icon for appimagetool
[ -f "${SCRIPT_DIR}/assets/mediarenamer_256.png" ] && \
    cp "${SCRIPT_DIR}/assets/mediarenamer_256.png" "${APP_DIR}/mediarenamer.png"

# AppRun — uses the bundled Python, sets PYTHONHOME so stdlib is found
# PYTHONHOME is the critical variable: it tells the bundled Python where its
# own stdlib lives inside the AppImage, making it fully self-contained.
cat > "${APP_DIR}/AppRun" << APPRUNEOF
#!/bin/bash
SELF="\$(readlink -f "\$0")"
HERE="\$(dirname "\${SELF}")"

# Point bundled Python at its own stdlib inside the AppImage
export PYTHONHOME="\${HERE}/usr"
export PATH="\${HERE}/usr/bin:\${PATH}"

# Qt plugins from the bundled PyQt6
_PYQT6_DIR="\$(ls -d "\${HERE}/usr/lib/python${PYTHON_VERSION}/site-packages/PyQt6" 2>/dev/null | head -1)"
[ -d "\${_PYQT6_DIR}/Qt6/plugins" ] && export QT_PLUGIN_PATH="\${_PYQT6_DIR}/Qt6/plugins"
export QT_QPA_PLATFORMTHEME=

# Mark as AppImage for the About dialog
export APPIMAGE="\${APPIMAGE:-appimage}"

exec "\${HERE}/usr/bin/python${PYTHON_VERSION}" \
    "\${HERE}/usr/share/mediarenamer/main.py" "\$@"
APPRUNEOF
chmod +x "${APP_DIR}/AppRun"

# ── 5. Build final AppImage ───────────────────────────────────────────────────
echo "[5/5] Building AppImage..."
OUTPUT="${SCRIPT_DIR}/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

# Get appimagetool — extract it (no FUSE needed)
TOOL_DIR="$(mktemp -d)"
wget -q "https://github.com/AppImage/appimagetool/releases/download/continuous/appimagetool-x86_64.AppImage" \
    -O "${TOOL_DIR}/appimagetool.AppImage"
chmod +x "${TOOL_DIR}/appimagetool.AppImage"
cd "${TOOL_DIR}"
"${TOOL_DIR}/appimagetool.AppImage" --appimage-extract >/dev/null 2>&1
cd "${SCRIPT_DIR}"
APPIMAGETOOL="${TOOL_DIR}/squashfs-root/AppRun"
[ -x "${APPIMAGETOOL}" ] || { echo "ERROR: appimagetool extraction failed"; rm -rf "${TOOL_DIR}"; exit 1; }

ARCH="${ARCH}" "${APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT}" 2>&1
BUILD_EXIT=$?
rm -rf "${TOOL_DIR}"

[ "${BUILD_EXIT}" -ne 0 ] && { echo "ERROR: appimagetool failed (exit ${BUILD_EXIT})"; exit "${BUILD_EXIT}"; }

chmod +x "${OUTPUT}"
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "  ✓ Built: ${OUTPUT}"
echo "  Size:  $(du -h "${OUTPUT}" | cut -f1)"
echo "  Run:   ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
echo "═══════════════════════════════════════════════════════════"
