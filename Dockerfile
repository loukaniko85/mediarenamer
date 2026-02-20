# ─────────────────────────────────────────────────────────────────────────────
# MediaRenamer — Docker image with full GUI support (X11 forwarding)
# Base: python:3.11-slim (Debian bookworm)
# ─────────────────────────────────────────────────────────────────────────────
FROM python:3.11-slim

LABEL org.opencontainers.image.title="MediaRenamer"
LABEL org.opencontainers.image.description="Rename movies & TV shows using TMDB — GUI via X11 forwarding"

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# ── System libraries ──────────────────────────────────────────────────────────
# PyQt6 bundles Qt itself but still requires the host X11/XCB layer.
# Missing any one of these causes "could not load the Qt platform plugin 'xcb'"
RUN apt-get update && apt-get install -y --no-install-recommends \
    # ── X11 core ──────────────────────────────────────────
    libx11-6 \
    libx11-xcb1 \
    libxext6 \
    libxi6 \
    libxtst6 \
    # ── XCB — every sub-library Qt's xcb platform plugin uses ──
    libxcb1 \
    libxcb-cursor0 \
    libxcb-glx0 \
    libxcb-icccm4 \
    libxcb-image0 \
    libxcb-keysyms1 \
    libxcb-randr0 \
    libxcb-render0 \
    libxcb-render-util0 \
    libxcb-shape0 \
    libxcb-shm0 \
    libxcb-sync1 \
    libxcb-util1 \
    libxcb-xfixes0 \
    libxcb-xinerama0 \
    libxcb-xkb1 \
    # ── XKB (keyboard layout) ─────────────────────────────
    libxkbcommon0 \
    libxkbcommon-x11-0 \
    # ── GL / EGL — Qt needs this even in software-render mode
    libgl1 \
    libegl1 \
    libgles2 \
    # ── Font rendering ────────────────────────────────────
    libfontconfig1 \
    libfreetype6 \
    fontconfig \
    fonts-dejavu-core \
    fonts-liberation \
    # ── GLib / D-Bus — used internally by Qt ─────────────
    libglib2.0-0 \
    libdbus-1-3 \
    # ── MediaInfo CLI (for media technical metadata) ──────
    mediainfo \
    # ── Certificates (for HTTPS to TMDB / OpenSubtitles) ─
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Rebuild font cache so Qt's font system finds the installed fonts
RUN fc-cache -fv

# ── Python dependencies ───────────────────────────────────────────────────────
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# ── Application source ────────────────────────────────────────────────────────
COPY core/      ./core/
COPY main.py    ./
COPY cli.py     ./
COPY config.py  ./

# ── Runtime environment ───────────────────────────────────────────────────────
# Force Qt to use the XCB (X11) platform plugin — this is what X11 forwarding uses.
ENV QT_QPA_PLATFORM=xcb

# Disable MIT-SHM; it is almost never available inside a container and causes
# a silent crash when Qt tries to use shared memory for pixmap transfers.
ENV QT_X11_NO_MITSHM=1

# Use software OpenGL so the container doesn't need a GPU or GL driver passthrough.
ENV LIBGL_ALWAYS_SOFTWARE=1

# Silence Qt accessibility warnings (no AT-SPI bus inside container)
ENV NO_AT_BRIDGE=1

# Settings / API keys are stored here; mount this directory to persist them.
VOLUME ["/root/.mediarenamer"]

# Mount your media files here
VOLUME ["/media"]

# ── Entrypoint ────────────────────────────────────────────────────────────────
# Default: launch the GUI.
# Override to use the CLI:
#   docker run ... mediarenamer python3 cli.py --help
ENTRYPOINT ["python3"]
CMD ["main.py"]
