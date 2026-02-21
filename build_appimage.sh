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

# ── 7. Build AppImage ─────────────────────────────────────────────────────────
echo "[6/6] Building AppImage with appimagetool..."
OUTPUT="${SCRIPT_DIR}/${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"

if command -v appimagetool &>/dev/null; then
    ARCH="${ARCH}" appimagetool "${APP_DIR}" "${OUTPUT}" 2>&1
    chmod +x "${OUTPUT}"
    echo ""
    echo "═══════════════════════════════════════════════════════════"
    echo "  ✓ AppImage built: ${OUTPUT}"
    echo "  Run: ./${APP_NAME}-${APP_VERSION}-${ARCH}.AppImage"
    echo "═══════════════════════════════════════════════════════════"
else
    echo ""
    echo "  ⚠ appimagetool not found — AppDir is ready at:"
    echo "    ${APP_DIR}"
    echo "  Install appimagetool from https://appimage.github.io/appimagetool/"
    echo "  Then run: appimagetool ${APP_DIR} ${OUTPUT}"
fi

# Cleanup temp dir
rm -rf "$(dirname "${APP_DIR}")"
