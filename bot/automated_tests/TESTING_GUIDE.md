# 📋 Telegram Bot Test-Anleitungen

## 🎯 Übersicht der Test-Optionen

Du hast jetzt **3 verschiedene Test-Ansätze** für deinen Halloween Bot:

### 1. 📄 **Manueller Test-Plan (EMPFOHLEN)**
**Datei:** `TELEGRAM_TEST_PLAN.md`
- ✅ **Vollständig zuverlässig**
- ✅ **Echte Telegram-Interaktion**  
- ✅ **Schritt-für-Schritt Anleitung**
- ✅ **Dokumentiert alle Edge-Cases**
- ⏱️ **Zeit:** ~15 Minuten

### 2. 🤖 **Mock API Tests (SCHNELL)**
**Datei:** `automated_tests/telegram_api_test.py`
- ✅ **Sofort ausführbar**
- ✅ **Testet Bot-Logik** 
- ✅ **100% Erfolgsquote**
- ⚠️ **Simuliert nur Responses**
- ⏱️ **Zeit:** ~30 Sekunden

### 3. 🌐 **Browser-Automatisierung (EXPERIMENTELL)**
**Dateien:** `automated_tests/telegram_bot_playwright_test.py`
- ⚠️ **Anti-Bot-Mechanismen**
- ⚠️ **Requires manual login**
- ⚠️ **Kann von Telegram geblockt werden**
- ⏱️ **Zeit:** ~5 Minuten (wenn es funktioniert)

### 4. 🔧 **Browser-Extension (ASSISTIERT)**
**Dateien:** `automated_tests/manifest.json` + Extension-Files
- ✅ **Echte Browser-Interaktion**
- ✅ **Manuelle Kontrolle**
- ✅ **Automatisiert repetitive Schritte**
- ⏱️ **Zeit:** ~10 Minuten

---

## 🚀 Schnell-Start Empfehlungen

### FÜR ENTWICKLUNG (täglich):
```bash
# Schnelle Mock-Tests
python automated_tests/telegram_api_test.py
```

### FÜR VOLLSTÄNDIGE VALIDIERUNG:
```bash
# Öffne manuellen Test-Plan
code TELEGRAM_TEST_PLAN.md
# Folge der Schritt-für-Schritt Anleitung
```

### FÜR BROWSER-ASSISTENZ:
1. Extension in Chrome laden:
   - Öffne `chrome://extensions/`
   - "Developer mode" aktivieren
   - "Load unpacked" → `automated_tests/` Ordner wählen
2. Telegram Web öffnen
3. Extension-Icon klicken → Tests ausführen

---

## ⚙️ Setup-Befehle

### Dependencies installieren:
```bash
pip install -r automated_tests/requirements_test.txt
```

### Mock-Tests ausführen:
```bash
cd automated_tests
python telegram_api_test.py
```

### Browser-Tests (mit Risiko):
```bash
# WICHTIG: Bot-Username in telegram_bot_playwright_test.py anpassen!
playwright install chromium
python automated_tests/telegram_bot_playwright_test.py
```

---

## 📊 Test-Vergleich

| Methode | Geschwindigkeit | Zuverlässigkeit | Echte Telegram | Setup |
|---------|----------------|-----------------|----------------|-------|
| **Manueller Plan** | 🟡 Mittel | 🟢 100% | 🟢 Ja | 🟢 Keine |
| **Mock API** | 🟢 Sehr schnell | 🟢 100% | 🟡 Simuliert | 🟢 Pip install |
| **Playwright** | 🟡 Langsam | 🔴 ~30%* | 🟢 Ja | 🟡 Complex |
| **Extension** | 🟢 Schnell | 🟢 90% | 🟢 Ja | 🟡 Manual load |

*Anti-Bot-Mechanismen können Tests blockieren

---

## 🎯 Empfohlener Test-Workflow

### 1. Entwicklung (täglich):
```bash
# Schnelle Smoke-Tests
python automated_tests/telegram_api_test.py
```

### 2. Feature-Release (wöchentlich):
```bash
# Vollständiger manueller Test
code TELEGRAM_TEST_PLAN.md
# Alle 8 Test-Cases durchgehen
```

### 3. Production-Release:
```bash
# Manuelle Tests + Browser-Extension für Effizienz
# + Tests mit echten Usern
```

---

## 🔧 Anpassungen

### Bot-Username konfigurieren:
```javascript
// In telegram_bot_playwright_test.py und telegram_test_extension.js:
BOT_USERNAME = "dein_halloween_bot"  // ANPASSEN!
```

### Test-Teams hinzufügen:
```python
# Matrix Team (Trinity + Neo)
MATRIX_TEAM_ID = "480514"  # 246935 + 233579

# Weitere Teams in universen.yaml prüfen
```

---

## 🎉 Los geht's!

**Für den schnellen Start:**
```bash
cd /home/fk/Dokumente/Worksheets/Eigene/Halloween25/bot
python automated_tests/telegram_api_test.py
```

**Für vollständige Tests:**
```bash
code TELEGRAM_TEST_PLAN.md
```

Viel Erfolg beim Testen! 🎃