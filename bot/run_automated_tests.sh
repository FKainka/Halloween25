#!/bin/bash
# Automatisierte Test-Ausführung für Halloween Bot

echo "🎃 Halloween Bot - Automatisierte Tests"
echo "======================================"

# Prüfe Dependencies
echo "📦 Prüfe Test-Dependencies..."
if ! python -c "import requests, pathlib" 2>/dev/null; then
    echo "📥 Installiere Test-Dependencies..."
    pip install -r automated_tests/requirements_test.txt
fi

# Test-Ordner erstellen
mkdir -p automated_tests/screenshots
mkdir -p automated_tests/reports

echo ""
echo "🧪 Verfügbare Tests:"
echo "1. Mock API Tests (schnell, kein echter Bot)"
echo "2. Playwright Browser Tests (langsam, benötigt Login)"
echo "3. Manueller Test-Plan (empfohlen)"
echo ""

read -p "Welchen Test ausführen? (1/2/3): " choice

case $choice in
    1)
        echo "🎭 Starte Mock API Tests..."
        cd automated_tests
        python telegram_api_test.py
        ;;
    2)
        echo "🌐 Starte Browser Tests..."
        echo "⚠️  WICHTIG: Bot-Username in telegram_bot_playwright_test.py konfigurieren!"
        echo "⚠️  Browser wird geöffnet - bitte manuell in Telegram einloggen"
        
        # Playwright installieren falls nötig
        if ! python -c "import playwright" 2>/dev/null; then
            pip install playwright
            playwright install chromium
        fi
        
        cd automated_tests  
        python telegram_bot_playwright_test.py
        ;;
    3)
        echo "📋 Öffne manuellen Test-Plan..."
        if command -v code &> /dev/null; then
            code TELEGRAM_TEST_PLAN.md
        else
            echo "📄 Öffne: TELEGRAM_TEST_PLAN.md"
            echo "   Folge den Schritten für manuelle Tests"
        fi
        ;;
    *)
        echo "❌ Ungültige Auswahl"
        exit 1
        ;;
esac

echo ""
echo "✅ Test-Ausführung abgeschlossen!"
echo "📊 Berichte in: automated_tests/reports/"
echo "📸 Screenshots in: automated_tests/screenshots/"