# MediaRenamer

**The open-source FileBot alternative** — rename and organise your movies, TV shows and Anime automatically.

Built by **loukaniko** with a little help from his LLM.

---

## What it does

MediaRenamer matches your messy media files against online databases (TheMovieDB, TheTVDB, AniDB) and renames them into clean, organised structures like:

```
Inception.2010.BluRay.1080p.x264.mkv
  →  Inception (2010).mkv

Breaking.Bad.S01E01.1080p.BluRay.mkv
  →  Breaking Bad/Season 1/Breaking Bad - S01E01 - Pilot.mkv
```

It comes with a **browser-based GUI** (via Docker + noVNC) and a full **REST API** for automation and batch processing.

---

## Features

### Core renaming
- Match movies, TV shows and anime against TMDB, TVDB, and AniDB
- Customisable naming schemes with `{n}`, `{y}`, `{s00e00}`, `{vf}`, `{vc}`, `{af}` tokens
- Built-in presets for **Plex**, **Kodi**, **Jellyfin**, **FileBot style**, and **Anime**
- **Dry-run mode** — preview every rename before committing
- **Copy mode** — keep originals, write renamed copies elsewhere
- Conflict detection — never silently overwrite existing files
- Full undo/redo with persistent history

### Batch & automation
- **REST API** with Swagger UI at `http://localhost:8060/docs`
- **Async batch jobs** — submit and poll, or set a webhook callback URL
- **API-only headless mode** — no GUI needed for NAS/server deployment
- CLI interface: `python3 cli.py --help`

### Extras
- Download poster/artwork images from TMDB
- Embed metadata tags into MP4/M4V files
- Fetch subtitles via OpenSubtitles
- Generate checksums (MD5, SHA1, SHA256) with optional sidecar files
- Language preference for metadata (20+ languages)
- Filter and search your file list
- Right-click: manual search, clear match, open containing folder

---

## Quick start (Docker — recommended)

```bash
docker build -t mediarenamer .

# Launch GUI + API
TMDB_API_KEY=your_key MEDIA_DIR=~/Movies ./docker-run.sh

# GUI in browser
open http://localhost:6080/vnc.html

# API docs
open http://localhost:8060/docs
```

Get a free TMDB API key at https://www.themoviedb.org/settings/api

See [DOCKER.md](DOCKER.md) for full platform-specific setup.

---

## Quick start (local Python)

```bash
pip install -r requirements.txt
export TMDB_API_KEY=your_key

python3 main.py          # GUI
uvicorn api.app:app      # API only
python3 cli.py --help    # CLI
```

---

## API at a glance

```bash
# Health
curl http://localhost:8060/api/v1/health

# Dry-run preview
curl -X POST http://localhost:8060/api/v1/media/rename \
  -H "Content-Type: application/json" \
  -d '{"files":["/media/Downloads/Movie.2024.mkv"],"dry_run":true}'

# Async batch job
curl -X POST http://localhost:8060/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"files":["/media/Downloads/"],"output_dir":"/media/Movies","operation":"move"}'
```

Full docs at [API.md](API.md) or `http://localhost:8060/docs`.

---

## Naming tokens

`{n}` title · `{y}` year · `{t}` episode title · `{s}` season · `{e}` episode ·
`{s00e00}` S01E01 · `{vf}` resolution · `{vc}` video codec · `{af}` audio codec · `{ac}` channels

---

## Credits

Built by **loukaniko** with a little help from his LLM.

Powered by [TheMovieDB](https://www.themoviedb.org/) · [TheTVDB](https://thetvdb.com/) · [FastAPI](https://fastapi.tiangolo.com/) · [PyQt6](https://www.riverbankcomputing.com/software/pyqt/) · [noVNC](https://novnc.com/)

MIT License
