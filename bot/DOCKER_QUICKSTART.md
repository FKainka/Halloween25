# 🎃 Halloween Bot - Docker Quick Reference

## Schnellstart (3 Schritte)

```bash
# 1. Environment konfigurieren
cp .env.example .env && nano .env

# 2. Bot starten
docker-compose up -d

# 3. Logs checken
docker-compose logs -f
```

## Wichtigste Befehle

```bash
# Mit Docker Compose
docker-compose up -d          # Bot starten
docker-compose down           # Bot stoppen
docker-compose logs -f        # Live-Logs
docker-compose restart        # Neu starten
docker-compose ps             # Status

# Mit Makefile (einfacher)
make up                       # Starten
make down                     # Stoppen
make logs                     # Live-Logs
make restart                  # Neu starten
make rebuild                  # Neu bauen & starten
make backup                   # Datenbank-Backup
make help                     # Alle Befehle
```

## Oder automatisches Setup-Script

```bash
./start-docker.sh             # Alles automatisch
```

## Persistente Daten

Diese Daten bleiben beim Neustart erhalten:
- `bot.db` - Datenbank mit Spielerdaten
- `photos/` - Alle hochgeladenen Fotos
- `logs/` - Bot-Logs

## Troubleshooting

```bash
# Logs prüfen
docker-compose logs --tail=100

# Container neu bauen
docker-compose down
docker-compose build --no-cache
docker-compose up -d

# In Container einloggen
docker-compose exec halloween-bot bash
```

## Backup vor Updates

```bash
# Datenbank sichern
make backup

# Oder manuell
cp bot.db bot.db.backup
```

📖 **Ausführliche Dokumentation:** [DOCKER.md](DOCKER.md)
