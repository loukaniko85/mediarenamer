# Running MediaRenamer in Docker

MediaRenamer is a desktop GUI app. Docker containers don't have screens, so the
container renders the window using your **host machine's X11 display server** —
the same approach used by many Linux GUI tools in containers.

---

## Quick start — Linux

This is the simplest case. X11 is already running.

```bash
# 1. Build the image (first run only, ~2 min)
docker build -t mediarenamer .

# 2. Allow the container to open a window on your desktop
xhost +local:docker

# 3. Launch
./docker-run.sh

# 4. (Optional) Revoke the xhost permission when you're done
xhost -local:docker
```

Or with docker compose:
```bash
xhost +local:docker
docker compose up
xhost -local:docker
```

---

## Quick start — macOS

You need **XQuartz** as macOS has no built-in X11 server.

```bash
# 1. Install XQuartz (once)
brew install --cask xquartz
# — or download from https://www.xquartz.org/

# 2. Open XQuartz, then go to:
#    XQuartz menu → Preferences → Security tab
#    Enable "Allow connections from network clients"
#    Quit and relaunch XQuartz.

# 3. Allow local connections
xhost +localhost

# 4. Build and launch
docker build -t mediarenamer .
./docker-run.sh
```

The script auto-detects XQuartz and sets `DISPLAY` to your loopback IP.

---

## Quick start — Windows

### Option A: WSL2 + WSLg (Windows 11 / recent Win10 — recommended)

WSLg provides a built-in X11/Wayland server. Run everything from a WSL2 terminal:

```bash
docker build -t mediarenamer .
./docker-run.sh
```

`DISPLAY` is set automatically by WSLg — no extra steps.

### Option B: VcXsrv (older Windows)

1. Download and install [VcXsrv](https://sourceforge.net/projects/vcxsrv/)
2. Launch **XLaunch**, choose *Multiple windows*, display `0`
3. On the *Extra settings* page, check **Disable access control**
4. Finish — the X server icon appears in the system tray
5. Find your Windows host IP (run `ipconfig` in cmd, look for your LAN IP)
6. In WSL2 / Git Bash:

```bash
export DISPLAY=<your-windows-ip>:0.0
docker build -t mediarenamer .
./docker-run.sh
```

---

## Persisting your API key

Your TMDB API key is saved inside the container at `/root/.mediarenamer/settings.json`.
The run script and compose file both mount `~/.mediarenamer` from your host to that
path, so the key survives across container restarts.

You can also pass the key as an environment variable (useful for CI or headless runs):

```bash
TMDB_API_KEY=your_key_here ./docker-run.sh
# or
export TMDB_API_KEY=your_key_here
docker compose up
```

---

## Mounting your media files

By default, `~/Media` on your host is mounted to `/media` inside the container.
Override with the `MEDIA_DIR` variable:

```bash
MEDIA_DIR=/mnt/nas/movies ./docker-run.sh
```

Inside the app, browse to `/media` to find your files.

---

## CLI mode (no display needed)

```bash
# Get help
./docker-run.sh cli --help

# Rename a directory of files
./docker-run.sh cli rename /media/Downloads/ --source tmdb
```

---

## Troubleshooting

### "could not load the Qt platform plugin 'xcb'"
The container is missing an xcb library OR can't connect to the X server.
Run with `QT_DEBUG_PLUGINS=1` to see which library is missing:

```bash
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -e QT_DEBUG_PLUGINS=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  mediarenamer python3 -c "from PyQt6.QtWidgets import QApplication; QApplication([])"
```

### "Authorization required, but no authorization protocol specified"
Run `xhost +local:docker` before launching the container.

### Window appears but is blank / black
Try adding `-e LIBGL_ALWAYS_SOFTWARE=1` to force software rendering:

```bash
docker run --rm \
  -e DISPLAY=$DISPLAY \
  -e LIBGL_ALWAYS_SOFTWARE=1 \
  -v /tmp/.X11-unix:/tmp/.X11-unix \
  mediarenamer
```

### macOS: "Can't open display"
1. Make sure XQuartz → Preferences → Security → **Allow connections from network clients** is checked
2. Restart XQuartz after changing that setting
3. Re-run `xhost +localhost`
4. Confirm `echo $DISPLAY` shows something like `localhost:0` or `/tmp/…`

### Windows: window doesn't appear
1. Make sure VcXsrv is running with **Disable access control** checked
2. Check Windows Firewall isn't blocking port 6000 (X11)
3. Try `DISPLAY=$(grep nameserver /etc/resolv.conf | awk '{print $2}'):0.0`

---

## Building a specific version

```bash
docker build --build-arg APP_VERSION=1.2.0 -t mediarenamer:1.2.0 .
```

## Running without GPU (pure software rendering)

Already the default — the image sets `LIBGL_ALWAYS_SOFTWARE=1`. This means
no GPU pass-through is needed but rendering may be slightly slower on 4K displays.
