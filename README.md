# MediaRenamer - FileBot Alternative

A free, open-source alternative to FileBot for renaming and organizing movies and TV shows. Runs as a standalone AppImage on Linux.

## Features

- 🎬 **Automatic File Matching**: Matches media files with online databases (TheMovieDB, TheTVDB)
- 📝 **Smart Renaming**: Rename files with customizable naming schemes
- 📺 **TV Show Support**: Handles TV shows with season/episode detection
- 🎞️ **Movie Support**: Matches movies by title and year
- 📥 **Subtitle Fetching**: Download subtitles from OpenSubtitles
- 🖱️ **Drag & Drop**: Easy-to-use GUI with drag and drop support
- 📦 **AppImage**: Single-file portable application
- 🎨 **Artwork Download**: Automatically download posters and fanart
- 📋 **Metadata Writing**: Write metadata tags to video files (MP4)
- ↩️ **Undo/Redo**: Track rename history and undo operations
- 💾 **Presets**: Save and load custom naming schemes
- 🔍 **Media Info**: Extract resolution, codec, audio format from files
- 🐳 **Docker Support**: Run in containers for batch processing

## Requirements

- Linux (x86_64)
- Python 3.8+ (for building from source)
- TheMovieDB API key (free): https://www.themoviedb.org/settings/api
- MediaInfo library (for technical metadata extraction):
  - Ubuntu/Debian: `sudo apt-get install mediainfo`
  - Fedora: `sudo dnf install mediainfo`
  - Or install via pip: `pip install pymediainfo` (includes bundled library on some platforms)
- Mutagen (for metadata writing): `pip install mutagen` (optional, for MP4 metadata)

## Quick Start

### Using the AppImage

1. Download the AppImage file
2. Make it executable: `chmod +x MediaRenamer-1.0.0-x86_64.AppImage`
3. Run it: `./MediaRenamer-1.0.0-x86_64.AppImage`

### Building from Source

1. Clone or download this repository
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys:
   - Edit `config.py` and add your TheMovieDB API key
   - Get a free API key from: https://www.themoviedb.org/settings/api

4. Run the application:
   ```bash
   python3 main.py
   ```

### Building AppImage

1. Install build dependencies:
   ```bash
   sudo apt-get install python3-venv python3-pip wget
   ```

2. Run the build script:
   ```bash
   chmod +x build_appimage.sh
   ./build_appimage.sh
   ```

3. The AppImage will be created in the current directory

### Docker

Images are published to GitHub Container Registry. Use the CLI for batch renaming:

```bash
# Pull (replace OWNER/REPO with your repo, e.g. myuser/mediarenamer)
docker pull ghcr.io/OWNER/REPO:main

# Run CLI: match and rename files in /path/to/media (dry run)
docker run --rm -e TMDB_API_KEY=your_key \
  -v /path/to/media:/data ghcr.io/OWNER/REPO:main \
  cli.py -i /data -o /data --dry-run

# Apply renames
docker run --rm -e TMDB_API_KEY=your_key \
  -v /path/to/media:/data ghcr.io/OWNER/REPO:main \
  cli.py -i /data -o /data -r
```

Build locally:

```bash
docker build -t mediarenamer .
docker run --rm -e TMDB_API_KEY=your_key -v /path/to/media:/data mediarenamer cli.py -i /data -o /data -r
```

### GitHub Actions (CI)

On push to `main`/`master` and on release:

- **AppImage**: Built and uploaded as an artifact; also attached to the release when you publish a release.
- **Docker**: Image is built and pushed to `ghcr.io/<your-username>/<repo-name>`.

Ensure the default branch is `main` or `master` (or adjust the workflow trigger). No extra secrets are required for GHCR push.

## Usage

### Basic Workflow

1. **Add Files**: Click "Add Files" or "Add Folder", or drag and drop files into the application
2. **Select Data Source**: Choose TheMovieDB or TheTVDB from the dropdown
3. **Match Files**: Click "Match Files" to automatically match your files with online databases
4. **Choose Naming Scheme**: Select a preset or customize the naming scheme
5. **Set Options**: 
   - Check "Download Artwork" to download poster images
   - Check "Write Metadata" to embed metadata in MP4 files
6. **Set Output Directory** (optional): Leave empty to rename in place, or specify a directory
7. **Rename**: Click "Rename Files" to apply the changes

### Advanced Features

**Presets:**
- Select a preset from the dropdown to quickly apply common naming schemes
- Click "Save Preset" to save your current naming scheme for future use
- Presets are stored in `~/.mediarenamer/presets.json`

**Undo/Redo:**
- After renaming, use "Undo" to revert the last operation
- Use "Redo" to re-apply an undone operation
- History is saved in `~/.mediarenamer/history.json`

**Artwork Download:**
- When enabled, downloads poster images (`.jpg`) to the same directory as renamed files
- Files are named: `{Title}_poster.jpg`

**Metadata Writing:**
- Embeds title, year, description, and other metadata into MP4/M4V files
- Adds poster as cover art when artwork download is enabled
- Requires `mutagen` library: `pip install mutagen`

### Naming Scheme Placeholders

**Basic Info:**
- `{n}` - Title/Name
- `{y}` - Year
- `{s}` - Season (e.g., S01)
- `{e}` - Episode (e.g., E01)
- `{s00e00}` - Season and Episode (e.g., S01E01)
- `{t}` - Episode title

**Media Information** (requires pymediainfo):
- `{vf}` or `{resolution}` - Video resolution (e.g., 1080p, 2160p)
- `{vc}` or `{video_codec}` - Video codec (e.g., AVC, HEVC)
- `{ac}` or `{audio_codec}` or `{af}` - Audio codec (e.g., DTS, AC3, AAC)
- `{channels}` - Audio channels (e.g., 5.1, 7.1)
- `{bit_depth}` - Video bit depth (e.g., 10bit)

### Examples

**Movies:**
- `{n} ({y})/{n} ({y})` → `The Matrix (1999)/The Matrix (1999).mp4`
- `{n} - {y}` → `The Matrix - 1999.mp4`
- `{n}.{y}.{vf}.{vc}.{ac}` → `The.Terminator.1984.1080p.AVC.DTS.mkv` (like FileBot!)

**TV Shows:**
- `{n}/Season {s}/{n} - {s00e00} - {t}` → `Breaking Bad/Season 1/Breaking Bad - S01E01 - Pilot.mkv`
- `{n}/S{s}/E{e}` → `Breaking Bad/S01/E01.mkv`
- `{n}.{s00e00}.{vf}.{vc}.{ac}` → `Breaking.Bad.S01E01.1080p.HEVC.AAC.mkv`

## API Keys

### TheMovieDB (Required)

1. Create a free account at https://www.themoviedb.org/
2. Go to Settings → API
3. Request an API key
4. Copy your API key to `config.py`

### TheTVDB (Optional)

Currently uses TheMovieDB as fallback. Full TheTVDB support requires API authentication setup.

### OpenSubtitles (Optional)

Subtitle fetching works without an API key but may have rate limits.

## Limitations

- Currently supports TheMovieDB as primary data source
- Subtitle fetching requires file hash matching (works best with popular files)
- TheTVDB integration is simplified (uses TMDB fallback)

## Troubleshooting

**No matches found:**
- Check your internet connection
- Verify your TheMovieDB API key in `config.py`
- Try cleaning up the filename (remove extra info, use standard format)

**AppImage won't run:**
- Make sure it's executable: `chmod +x MediaRenamer-*.AppImage`
- Check if you have FUSE installed: `sudo apt-get install fuse`

**Build fails:**
- Ensure you have Python 3.8+ installed
- Install build dependencies: `sudo apt-get install python3-venv python3-pip wget mediainfo`

**Media info not extracted:**
- Install MediaInfo library: `sudo apt-get install mediainfo` (or `sudo dnf install mediainfo` on Fedora)
- Or ensure pymediainfo is installed: `pip install pymediainfo`
- Media info extraction is optional - the app will work without it, just without technical metadata in filenames

## License

This project is open source and free to use.

## Contributing

Contributions are welcome! Feel free to submit issues or pull requests.

## Acknowledgments

- TheMovieDB for providing free API access
- OpenSubtitles for subtitle database
- PyQt6 for the GUI framework
