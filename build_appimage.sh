#!/bin/bash
# Build script for creating AppImage

set -e

APP_NAME="MediaRenamer"
APP_VERSION="1.0.0"
APP_DIR="AppDir"
BUILD_DIR="build"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo "Building $APP_NAME AppImage..."

# Clean previous builds
rm -rf "$APP_DIR" "$BUILD_DIR"
mkdir -p "$APP_DIR" "$BUILD_DIR"

# Create AppDir structure
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/scalable/apps"
mkdir -p "$APP_DIR/usr/lib"

# Install Python dependencies in a virtual environment
echo "Setting up Python environment..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r "$SCRIPT_DIR/requirements.txt"
pip install pyinstaller

# -----------------------------------------------------------------------
# Write the complete PyInstaller spec file.
# IMPORTANT: pyz and exe sections MUST be inside a single heredoc.
# Using a non-expanded delimiter (SPECEOF) to prevent shell variable
# expansion inside the spec's Python code.
# -----------------------------------------------------------------------
cat > "$BUILD_DIR/app.spec" << 'SPECEOF'
# -*- mode: python ; coding: utf-8 -*-
import sys, os
sys.path.insert(0, os.path.abspath('..'))

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[os.path.abspath('..')],
    binaries=[],
    datas=[],
    hiddenimports=[
        'PyQt6.QtCore',
        'PyQt6.QtGui',
        'PyQt6.QtWidgets',
        'PyQt6.sip',
        'core.matcher',
        'core.renamer',
        'core.subtitle_fetcher',
        'core.history',
        'core.presets',
        'core.artwork',
        'core.metadata_writer',
        'core.media_info',
        'pymediainfo',
        'requests',
        'certifi',
        'charset_normalizer',
        'idna',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='mediarenamer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
SPECEOF

# Build with PyInstaller (run from build dir so ../main.py resolves correctly)
echo "Building executable..."
cd "$BUILD_DIR"
pyinstaller app.spec
cd "$SCRIPT_DIR"

if [ ! -f "$BUILD_DIR/dist/mediarenamer" ]; then
    echo "Error: PyInstaller executable not found"
    exit 1
fi

cp "$BUILD_DIR/dist/mediarenamer" "$APP_DIR/usr/bin/mediarenamer"
chmod +x "$APP_DIR/usr/bin/mediarenamer"

# -----------------------------------------------------------------------
# Desktop file
# appimagetool REQUIRES the .desktop file at the AppDir root.
# It also should live in usr/share/applications/ for system integration.
# -----------------------------------------------------------------------
cat > "$APP_DIR/mediarenamer.desktop" << 'DESKTOPEOF'
[Desktop Entry]
Name=MediaRenamer
Comment=Rename movies and TV shows using online databases
Exec=mediarenamer
Icon=mediarenamer
Type=Application
Categories=AudioVideo;Video;Utility;
Keywords=rename;media;movies;tv;
DESKTOPEOF
cp "$APP_DIR/mediarenamer.desktop" "$APP_DIR/usr/share/applications/mediarenamer.desktop"

# -----------------------------------------------------------------------
# Icon
# appimagetool also looks for an icon at AppDir root.
# For production, replace this SVG with a proper 256x256 PNG.
# -----------------------------------------------------------------------
cat > "$APP_DIR/usr/share/icons/hicolor/scalable/apps/mediarenamer.svg" << 'SVGEOF'
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" rx="32" fill="#1565C0"/>
  <rect x="40" y="80"  width="176" height="16" rx="8" fill="white" opacity="0.9"/>
  <rect x="40" y="112" width="140" height="16" rx="8" fill="white" opacity="0.7"/>
  <rect x="40" y="144" width="160" height="16" rx="8" fill="white" opacity="0.9"/>
  <rect x="40" y="176" width="120" height="16" rx="8" fill="white" opacity="0.7"/>
  <circle cx="196" cy="180" r="40" fill="#42A5F5"/>
  <path d="M184 165 L216 180 L184 195 Z" fill="white"/>
</svg>
SVGEOF
cp "$APP_DIR/usr/share/icons/hicolor/scalable/apps/mediarenamer.svg" "$APP_DIR/mediarenamer.svg"

# -----------------------------------------------------------------------
# AppRun entry point
# -----------------------------------------------------------------------
cat > "$APP_DIR/AppRun" << 'APPRUNEOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/mediarenamer" "$@"
APPRUNEOF
chmod +x "$APP_DIR/AppRun"

# -----------------------------------------------------------------------
# Download appimagetool if needed
# -----------------------------------------------------------------------
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# -----------------------------------------------------------------------
# Create AppImage
# ARCH must be set explicitly; appimagetool uses it in the output filename.
# -----------------------------------------------------------------------
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APP_DIR" "${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

echo ""
echo "Done! Created: ${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
