#!/bin/bash
# Build script for creating AppImage

set -e

APP_NAME="MediaRenamer"
APP_VERSION="1.0.0"
APP_DIR="AppDir"
BUILD_DIR="build"

echo "Building $APP_NAME AppImage..."

# Clean previous builds
rm -rf "$APP_DIR" "$BUILD_DIR"
mkdir -p "$APP_DIR" "$BUILD_DIR"

# Create AppDir structure
mkdir -p "$APP_DIR/usr/bin"
mkdir -p "$APP_DIR/usr/share/applications"
mkdir -p "$APP_DIR/usr/share/icons/hicolor/256x256/apps"
mkdir -p "$APP_DIR/usr/lib"

# Install Python dependencies in a virtual environment
echo "Setting up Python environment..."
python3 -m venv "$BUILD_DIR/venv"
source "$BUILD_DIR/venv/bin/activate"
pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

# Create PyInstaller spec file
cat > "$BUILD_DIR/app.spec" <<'EOF'
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['../main.py'],
    pathex=[],
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
EOF

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
    upx=False,  # Disable UPX for CI compatibility (UPX may not be available)
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
EOF

# Build with PyInstaller
echo "Building executable..."
cd "$BUILD_DIR"
pyinstaller app.spec
cd ..

# Copy executable to AppDir
if [ ! -f "$BUILD_DIR/dist/mediarenamer" ]; then
    echo "Error: PyInstaller executable not found!"
    exit 1
fi

cp "$BUILD_DIR/dist/mediarenamer" "$APP_DIR/usr/bin/mediarenamer"
chmod +x "$APP_DIR/usr/bin/mediarenamer"

# PyInstaller bundles everything needed, but we may need Qt plugins
# Copy Qt plugins if they exist
if [ -d "$BUILD_DIR/dist/mediarenamer" ]; then
    # PyInstaller creates a directory with all dependencies
    # We need to copy the entire dist directory structure
    echo "Note: PyInstaller should have bundled all dependencies"
fi

# Create desktop file
cat > "$APP_DIR/usr/share/applications/mediarenamer.desktop" <<EOF
[Desktop Entry]
Name=MediaRenamer
Comment=FileBot alternative for renaming movies and TV shows
Exec=mediarenamer
Icon=mediarenamer
Type=Application
Categories=AudioVideo;Video;
EOF

# Create icon (simple placeholder - users can replace with their own)
# For now, we'll create a simple SVG icon
mkdir -p "$APP_DIR/usr/share/icons/hicolor/scalable/apps"
cat > "$APP_DIR/usr/share/icons/hicolor/scalable/apps/mediarenamer.svg" <<EOF
<svg xmlns="http://www.w3.org/2000/svg" width="256" height="256" viewBox="0 0 256 256">
  <rect width="256" height="256" fill="#2196F3"/>
  <text x="128" y="180" font-family="Arial" font-size="80" fill="white" text-anchor="middle">MR</text>
</svg>
EOF

# Create AppRun script
cat > "$APP_DIR/AppRun" <<'EOF'
#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export LD_LIBRARY_PATH="${HERE}/usr/lib:${LD_LIBRARY_PATH}"
exec "${HERE}/usr/bin/mediarenamer" "$@"
EOF
chmod +x "$APP_DIR/AppRun"

# Download appimagetool if not present
if [ ! -f "appimagetool-x86_64.AppImage" ]; then
    echo "Downloading appimagetool..."
    wget -q "https://github.com/AppImage/AppImageKit/releases/download/continuous/appimagetool-x86_64.AppImage"
    chmod +x appimagetool-x86_64.AppImage
fi

# Create AppImage
echo "Creating AppImage..."
ARCH=x86_64 ./appimagetool-x86_64.AppImage "$APP_DIR" "${APP_NAME}-${APP_VERSION}-x86_64.AppImage"

echo "Done! AppImage created: ${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
echo "Make it executable: chmod +x ${APP_NAME}-${APP_VERSION}-x86_64.AppImage"
