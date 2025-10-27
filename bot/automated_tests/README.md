# 🚀 Automatisierte Telegram Bot Tests

Dieses Verzeichnis enthält automatisierte Tests für den Halloween Bot über die Telegram Web-App.

## 📋 Setup

### 1. Dependencies installieren

```bash
pip install selenium playwright pytest-playwright beautifulsoup4
```

### 2. Browser-Driver installieren

```bash
# Für Playwright (empfohlen)
playwright install chromium

# Oder für Selenium
# Lade ChromeDriver: https://chromedriver.chromium.org/
```

### 3. Telegram Web-App Login

1. Öffne https://web.telegram.org
2. Melde dich an
3. Suche deinen Bot
4. Kopiere die Chat-URL für die Tests

## 🧪 Test-Ausführung

### Einzelne Tests
```bash
# Playwright Tests
pytest telegram_bot_playwright_test.py -v

# Selenium Tests  
python telegram_bot_selenium_test.py
```

### Alle Tests
```bash
pytest automated_tests/ -v --html=test_report.html
```

## 📁 Dateien

- `telegram_bot_playwright_test.py` - Playwright-basierte Tests (modern, schnell)
- `telegram_bot_selenium_test.py` - Selenium-basierte Tests (klassisch)
- `test_config.py` - Konfiguration und Test-Daten
- `test_helpers.py` - Hilfs-Funktionen
- `requirements_test.txt` - Test-Dependencies

## ⚙️ Konfiguration

Erstelle eine `.env.test` Datei:

```env
TELEGRAM_WEB_URL=https://web.telegram.org/k/#@your_bot_name
BOT_USERNAME=your_bot_username
TEST_USER_PHONE=+49123456789
ADMIN_USER_ID=123456789
HEADLESS=false
SCREENSHOT_PATH=./screenshots/
```

## 🔧 Browser-Automatisierung Einschränkungen

**Wichtig:** Telegram Web-App hat starke Anti-Bot-Mechanismen:

1. **CAPTCHA**: Bei automatisierten Aktionen
2. **Rate-Limiting**: Zu schnelle Nachrichten werden geblockt  
3. **Session-Validation**: Login-Sessions können ungültig werden
4. **CloudFlare**: Zusätzlicher Bot-Schutz

**Alternative Ansätze:**
- **Telegram Bot API**: Direkter API-Test ohne Browser
- **Mock-Telegram**: Fake Telegram-Server für Tests
- **Manueller Browser**: Browser-Extension für assistierte Tests

## 📱 Mobile App Alternative

Für echte Mobile-Tests:
```bash
# Appium für Android/iOS
pip install appium-python-client
```

## 🎯 Test-Coverage

- [x] Bot-Registrierung (/start)
- [x] Hilfe-Command (/help) 
- [x] Punkte-Anzeige (/punkte)
- [x] Team-Beitritt (/teamid)
- [x] Foto-Upload (Party/Film/Puzzle)
- [x] Fehlerbehandlung
- [x] Admin-Commands (optional)

## 📊 Reporting

Tests erstellen automatisch:
- Screenshots bei Fehlern
- HTML Test-Report
- Performance-Metriken
- Fehler-Logs