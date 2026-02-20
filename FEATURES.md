# MediaRenamer Features

## Core Features

### File Matching
- **Automatic Matching**: Matches files with TheMovieDB and TheTVDB databases
- **Smart Parsing**: Extracts title, year, season, and episode from filenames
- **Multiple Results**: Search returns multiple matches for manual selection (API support)
- **Fallback Matching**: Falls back to alternative data sources if primary match fails

### Renaming
- **Customizable Schemes**: Use placeholders to create any naming pattern
- **Media Info Integration**: Automatically includes resolution, codec, audio format
- **FileBot Compatible**: Supports FileBot-style naming schemes
- **Batch Processing**: Rename hundreds of files at once

### Media Information
- **Technical Metadata**: Extracts resolution (1080p, 4K), video codec (AVC, HEVC), audio codec (DTS, AC3)
- **File Analysis**: Reads actual file properties, not just filename
- **Optional**: Works without MediaInfo, just without technical details

## Advanced Features

### Undo/Redo System
- **Rename History**: Tracks all rename operations
- **Undo Support**: Revert any rename operation
- **Redo Support**: Re-apply undone operations
- **Persistent Storage**: History saved to `~/.mediarenamer/history.json`
- **100 Operation Limit**: Keeps last 100 operations for performance

### Preset Management
- **Built-in Presets**: 10+ common naming schemes included
- **Custom Presets**: Save your own naming schemes
- **Quick Access**: Dropdown menu for instant preset selection
- **Persistent Storage**: Presets saved to `~/.mediarenamer/presets.json`

### Artwork Download
- **Poster Images**: Downloads movie/TV show posters from TMDB
- **Automatic Naming**: Names files as `{Title}_poster.jpg`
- **Same Directory**: Saves artwork next to renamed media files
- **Optional**: Enable/disable per operation

### Metadata Writing
- **MP4 Support**: Writes metadata to MP4/M4V files
- **Embedded Info**: Title, year, description, genres
- **Cover Art**: Embeds poster images as cover art
- **TV Show Metadata**: Season/episode information
- **Requires Mutagen**: Install with `pip install mutagen`

### Subtitle Fetching
- **OpenSubtitles Integration**: Downloads subtitles automatically
- **Hash Matching**: Uses file hash for perfect matches
- **Multiple Formats**: Supports SRT, ASS, SUB formats
- **Same Directory**: Saves subtitles next to media files

## User Interface Features

### Drag & Drop
- **File Drop**: Drag files directly into the application
- **Folder Drop**: Drop entire folders to process recursively
- **Visual Feedback**: Clear indication of dropped items

### Progress Tracking
- **Real-time Progress**: Progress bar shows operation status
- **Status Messages**: Detailed messages for each operation
- **Error Reporting**: Clear error messages for failed operations

### Preview Before Rename
- **Side-by-Side View**: See original and new names side by side
- **Live Preview**: Updates as you change naming scheme
- **Match Status**: Shows which files matched successfully

## CLI Features

### Batch Processing
- **Recursive Scanning**: Process entire directory trees
- **Dry Run Mode**: Preview changes without applying
- **Output Directory**: Specify where to save renamed files
- **Quiet Mode**: Minimal output for scripting

### Docker Support
- **Containerized**: Run in Docker containers
- **Headless Mode**: No GUI required for batch processing
- **Volume Mounting**: Process files from host system
- **Environment Variables**: Configure API keys via env vars

## Technical Features

### AppImage Support
- **Portable**: Single-file application
- **No Installation**: Just download and run
- **Self-contained**: Includes all dependencies
- **Universal**: Works on any Linux distribution

### GitHub Actions Integration
- **Automated Builds**: Builds on every push
- **Release Assets**: Attaches AppImage to releases
- **Docker Registry**: Pushes to GitHub Container Registry
- **No Secrets Required**: Uses GitHub token for registry

## File Organization

### Folder Structure
- **Plex Compatible**: Creates Plex-standard folder structures
- **Customizable**: Use placeholders to create any structure
- **Nested Directories**: Supports multi-level directory creation
- **Automatic Creation**: Creates directories as needed

### File Handling
- **Safe Renaming**: Checks for existing files before renaming
- **Error Handling**: Graceful handling of permission errors
- **Path Validation**: Validates file paths before operations
- **Cross-platform**: Works on Linux, macOS (with modifications)

## Data Sources

### TheMovieDB
- **Primary Source**: Main database for movies and TV shows
- **Free API**: No cost for API access
- **Rich Metadata**: Detailed information including overviews
- **Poster Artwork**: High-quality poster images

### TheTVDB
- **TV Focused**: Specialized TV show database
- **Fallback Support**: Uses TMDB if TVDB unavailable
- **Episode Details**: Detailed episode information

## Configuration

### API Keys
- **Environment Variables**: Set via `TMDB_API_KEY` env var
- **Config File**: Edit `config.py` for persistent storage
- **Docker**: Pass via `-e TMDB_API_KEY=...`

### Settings Storage
- **User Directory**: Stores settings in `~/.mediarenamer/`
- **JSON Format**: Human-readable configuration files
- **Portable**: Can be copied between systems

## Future Enhancements (Potential)

- **Manual Match Selection**: GUI for choosing from multiple matches
- **Watch Folders**: Automatically process new files
- **Scheduled Tasks**: Cron-like scheduling
- **RSS Integration**: Process downloads automatically
- **Duplicate Detection**: Find and handle duplicate files
- **File Validation**: Check file integrity
- **Quality Detection**: Identify video quality automatically
- **Language Preferences**: Set preferred metadata language
- **Export/Import**: Share configurations between users
