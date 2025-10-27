# Docker Setup für Halloween Bot

## Schnellstart

### 1. Environment-Variablen konfigurieren

```bash
# .env.example kopieren und anpassen
cp .env.example .env
nano .env  # oder ein anderer Editor
```

Mindestens diese Werte setzen:
- `TELEGRAM_BOT_TOKEN` - Von @BotFather
- `OPENAI_API_KEY` - Für Bildanalyse
- `ADMIN_USER_IDS` - Deine Telegram User ID

### 2. Bot mit Docker Compose starten

```bash
# Bot bauen und starten
docker-compose up -d

# Logs anzeigen
docker-compose logs -f

# Bot stoppen
docker-compose down
```

### 3. Bot neu starten nach Code-Änderungen

```bash
# Rebuild und Restart
docker-compose up -d --build

# Oder komplett neu
docker-compose down
docker-compose up -d --build
```

## Manuelle Docker-Befehle

Falls du Docker Compose nicht nutzen möchtest:

```bash
# Image bauen
docker build -t halloween-bot .

# Container starten
docker run -d \
  --name halloween-bot \
  --env-file .env \
  -v $(pwd)/bot.db:/app/bot.db \
  -v $(pwd)/photos:/app/photos \
  -v $(pwd)/logs:/app/logs \
  -v $(pwd)/../notes/universen.yaml:/app/../notes/universen.yaml:ro \
  -v $(pwd)/templates:/app/templates:ro \
  --restart unless-stopped \
  halloween-bot

# Logs anzeigen
docker logs -f halloween-bot

# Container stoppen
docker stop halloween-bot

# Container entfernen
docker rm halloween-bot
```

## Daten-Persistenz

Folgende Daten werden persistent gespeichert (als Volumes):
- `bot.db` - SQLite-Datenbank mit allen Spielerdaten
- `photos/` - Hochgeladene Fotos (Party, Films, Puzzles)
- `logs/` - Bot-Logs
- `universen.yaml` - Film-Konfiguration (read-only)
- `templates/` - Nachrichtenvorlagen (read-only)

## Wartung

### Logs anzeigen
```bash
# Live-Logs
docker-compose logs -f

# Letzte 100 Zeilen
docker-compose logs --tail=100
```

### Container-Status prüfen
```bash
docker-compose ps
```

### In Container einloggen (Debugging)
```bash
docker-compose exec halloween-bot bash
```

### Datenbank-Backup erstellen
```bash
# Bot stoppen
docker-compose stop

# Backup erstellen
cp bot.db bot.db.backup-$(date +%Y%m%d-%H%M%S)

# Bot wieder starten
docker-compose start
```

### Logs rotieren
Die Logs werden automatisch rotiert (max. 3 Dateien à 10MB).

## Troubleshooting

### Bot startet nicht
```bash
# Logs prüfen
docker-compose logs halloween-bot

# Häufige Probleme:
# - TELEGRAM_BOT_TOKEN fehlt oder ungültig
# - OPENAI_API_KEY fehlt
# - Berechtigungsprobleme bei Volumes
```

### Berechtigungsprobleme
```bash
# Volumes dem aktuellen User zuweisen
sudo chown -R $USER:$USER photos logs bot.db
```

### Container neu bauen (Fresh Start)
```bash
# Alles entfernen und neu bauen
docker-compose down -v
docker-compose build --no-cache
docker-compose up -d
```

## Production-Setup

### Mit SSL/TLS (empfohlen für Production)

Für Webhook-Setup mit HTTPS (statt Polling):

```yaml
# docker-compose.yml erweitern
services:
  halloween-bot:
    # ... existing config ...
    environment:
      - WEBHOOK_URL=https://yourdomain.com/webhook
      - WEBHOOK_PORT=8443
    ports:
      - "8443:8443"
```

### Monitoring

```bash
# Healthcheck-Status prüfen
docker inspect halloween-bot | grep -A 5 Health

# Resource-Nutzung überwachen
docker stats halloween-bot
```

## Entwicklung

### Hot-Reload für Development
```yaml
# docker-compose.dev.yml
version: '3.8'
services:
  halloween-bot:
    build: .
    volumes:
      - .:/app  # Code-Verzeichnis mounten für Live-Reload
      - ./bot.db:/app/bot.db
      - ./photos:/app/photos
    environment:
      - ENVIRONMENT=development
      - LOG_LEVEL=DEBUG
```

Dann:
```bash
docker-compose -f docker-compose.dev.yml up
```

## Sicherheit

- **Niemals** `.env` in Git committen
- Bot läuft als non-root User (UID 1000)
- Read-only Mounts für Config-Dateien
- Automatische Log-Rotation begrenzt Disk-Usage
- Healthchecks für automatische Container-Restarts
