#!/bin/bash
# Quick Start Script für Halloween Bot mit Docker

set -e

echo "🎃 Halloween Bot - Docker Setup 🎃"
echo ""

# Prüfen ob Docker installiert ist
if ! command -v docker &> /dev/null; then
    echo "❌ Docker ist nicht installiert!"
    echo "Installiere Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose ist nicht installiert!"
    echo "Installiere Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

# Prüfen ob .env existiert
if [ ! -f .env ]; then
    echo "📝 Erstelle .env Datei..."
    cp .env.example .env
    echo ""
    echo "⚠️  WICHTIG: Bitte konfiguriere die .env Datei!"
    echo ""
    echo "Erforderliche Werte:"
    echo "  - TELEGRAM_BOT_TOKEN (von @BotFather)"
    echo "  - OPENAI_API_KEY (für Bildanalyse)"
    echo "  - ADMIN_USER_IDS (deine Telegram User ID)"
    echo ""
    read -p "Möchtest du die .env jetzt bearbeiten? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        ${EDITOR:-nano} .env
    else
        echo "Bitte bearbeite .env manuell bevor du den Bot startest!"
        exit 0
    fi
fi

# Prüfen ob wichtige Werte gesetzt sind
if grep -q "your_bot_token_here" .env; then
    echo "⚠️  TELEGRAM_BOT_TOKEN ist noch nicht gesetzt!"
    echo "Bitte bearbeite die .env Datei."
    exit 1
fi

if grep -q "your_openai_api_key_here" .env; then
    echo "⚠️  OPENAI_API_KEY ist noch nicht gesetzt!"
    echo "Bitte bearbeite die .env Datei."
    exit 1
fi

# Verzeichnisse erstellen
echo "📁 Erstelle Verzeichnisse..."
mkdir -p photos/party photos/films photos/puzzles photos/thumbnails
mkdir -p logs
mkdir -p backups

# Docker Image bauen
echo "🔨 Baue Docker Image..."
docker-compose build

# Bot starten
echo "🚀 Starte Bot..."
docker-compose up -d

# Warten bis Bot läuft
echo "⏳ Warte auf Bot-Start..."
sleep 3

# Status prüfen
if docker-compose ps | grep -q "Up"; then
    echo ""
    echo "✅ Bot läuft erfolgreich!"
    echo ""
    echo "Nützliche Befehle:"
    echo "  docker-compose logs -f          # Live-Logs anzeigen"
    echo "  docker-compose stop             # Bot stoppen"
    echo "  docker-compose restart          # Bot neu starten"
    echo "  docker-compose down             # Bot stoppen und entfernen"
    echo ""
    echo "Oder mit Makefile:"
    echo "  make logs                       # Live-Logs"
    echo "  make restart                    # Neu starten"
    echo "  make help                       # Alle Befehle"
    echo ""
    read -p "Möchtest du die Logs jetzt anzeigen? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        docker-compose logs -f
    fi
else
    echo "❌ Fehler beim Starten des Bots!"
    echo "Prüfe die Logs mit: docker-compose logs"
    exit 1
fi
