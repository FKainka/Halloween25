# Halloween Bot Dockerfile
FROM python:3.11-slim

# Arbeitsverzeichnis erstellen
WORKDIR /app

# System-Dependencies installieren (für Pillow/Image Processing)
RUN apt-get update && apt-get install -y \
    gcc \
    libjpeg-dev \
    zlib1g-dev \
    && rm -rf /var/lib/apt/lists/*

# Python-Dependencies installieren
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Bot-Code kopieren
COPY . .

# Verzeichnisse für persistente Daten erstellen
RUN mkdir -p /app/photos/party /app/photos/films /app/photos/puzzles /app/photos/thumbnails \
    && mkdir -p /app/logs

# Bot als non-root User ausführen
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Healthcheck
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import os; exit(0 if os.path.exists('/app/bot.db') else 1)"

# Bot starten
CMD ["python3", "main.py"]
