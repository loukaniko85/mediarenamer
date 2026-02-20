# MediaRenamer - Docker image (CLI + optional GUI with X11)
FROM python:3.11-slim

LABEL org.opencontainers.image.description="FileBot alternative - rename movies and TV shows"

ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

# Install MediaInfo library and optional GUI dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    mediainfo \
    libxkbcommon0 libxcb-cursor0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt || \
    (pip install --no-cache-dir PyQt6 requests pymediainfo mutagen 2>/dev/null || \
     pip install --no-cache-dir PyQt6 requests pymediainfo)

COPY core/ ./core/
COPY main.py cli.py config.py ./

# Default: run CLI. For GUI: docker run -e DISPLAY -v /tmp/.X11-unix:/tmp/.X11-unix image main.py
ENTRYPOINT ["python3"]
CMD ["cli.py", "--help"]
