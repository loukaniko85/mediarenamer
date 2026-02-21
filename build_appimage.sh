#!/bin/bash
# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer AppImage builder
#
# Usage:
#   ./build_appimage.sh [--arch aarch64]
#
# Requirements:
#   apt install appimagetool libfuse2 python3 python3-pip
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
APP_DIR="$(mktemp -d)/${APP_NAME}.AppDir"
mkdir -p "${APP_DIR}/usr/bin"
mkdir -p "${APP_DIR}/usr/lib/python3"
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
    "${SCRIPT_DIR}/" "${APP_DIR}/usr/lib/mediarenamer/"

# ── 3. Install Python dependencies ───────────────────────────────────────────
echo "[2/6] Installing Python dependencies into AppDir..."
pip3 install --target="${APP_DIR}/usr/lib/python3" \
    PyQt6 requests pymediainfo mutagen \
    --quiet 2>&1 | tail -3

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
        echo "  ⚠ assets/mediarenamer_${SIZE}.png not found — skipping ${SIZE}×${SIZE}"
    fi
done

# AppImage root icon (required by appimagetool — must be 256px PNG)
if [ -f "${SCRIPT_DIR}/assets/mediarenamer_256.png" ]; then
    cp "${SCRIPT_DIR}/assets/mediarenamer_256.png" "${APP_DIR}/mediarenamer.png"
    echo "  ✓ Root icon (256px)"
elif [ -f "${SCRIPT_DIR}/assets/mediarenamer.png" ]; then
    cp "${SCRIPT_DIR}/assets/mediarenamer.png" "${APP_DIR}/mediarenamer.png"
    echo "  ✓ Root icon (fallback)"
else
    echo "  ⚠ WARNING: No root icon found — AppImage icon may be missing in desktop"
fi

# ── 6. AppRun launcher ────────────────────────────────────────────────────────
echo "[5/6] Writing AppRun launcher..."
cat > "${APP_DIR}/AppRun" << 'APPRUNEOF'
#!/bin/bash
SELF="$(readlink -f "$0")"
HERE="$(dirname "${SELF}")"
APPDIR="${HERE}"

# Inject bundled Python libs
export PYTHONPATH="${APPDIR}/usr/lib/python3:${PYTHONPATH}"
export PATH="${APPDIR}/usr/bin:${PATH}"

# Qt settings
export QT_QPA_PLATFORMTHEME=
export FONTCONFIG_FILE="${APPDIR}/usr/lib/fontconfig/fonts.conf"

# Mark as AppImage so GUI shows correct info
export APPIMAGE="${APPIMAGE:-appimage}"

exec python3 "${APPDIR}/usr/lib/mediarenamer/main.py" "$@"
APPRUNEOF
chmod +x "${APP_DIR}/AppRun"

# ── 7. Ensure appimagetool is available ──────────────────────────────────────
# appimagetool is itself an AppImage. On systems without FUSE (e.g. GitHub
# Actions), we extract it with --appimage-extract and run the inner binary.
# If it's already on PATH we use it directly; otherwise we download + extract.
echo "[6/6] Building AppImage with appimagetool..."
OUTPUT="${SCRIPT_DIR}/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

_APPIMAGETOOL=""

# Check if a working appimagetool is already on PATH
if command -v appimagetool &>/dev/null && appimagetool --version &>/dev/null 2>&1; then
    _APPIMAGETOOL="appimagetool"
    echo "      Using system appimagetool: $(appimagetool --version 2>&1 | head -1)"
else
    # Download and extract — works with or without FUSE
    echo "      appimagetool not on PATH — downloading..."
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
        echo "ERROR: appimagetool extraction failed — ${_APPIMAGETOOL} not found"
        ls -la "${_TOOL_DIR}/squashfs-root/" 2>/dev/null || echo "squashfs-root missing"
        rm -rf "${_TOOL_DIR}" "$(dirname "${APP_DIR}")"
        exit 1
    fi
    echo "      appimagetool ready: $("${_APPIMAGETOOL}" --version 2>&1 | head -1)"
fi

# ── Build ─────────────────────────────────────────────────────────────────────
ARCH="${ARCH}" "${_APPIMAGETOOL}" "${APP_DIR}" "${OUTPUT}" 2>&1
BUILD_EXIT=$?

# Cleanup temp dirs
[ -n "${_TOOL_DIR:-}" ] && rm -rf "${_TOOL_DIR}"
rm -rf "$(dirname "${APP_DIR}")"

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
