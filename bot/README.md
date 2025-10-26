# Halloween 2025 - Rebellion Bot

Telegram-Bot für die Halloween-Party 2025: "Rebellion gegen die KI"

## 🚀 Setup

### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

### 2. Bot bei BotFather registrieren

1. Öffne Telegram und suche nach `@BotFather`
2. Sende `/newbot`
3. Folge den Anweisungen und wähle einen Namen
4. Kopiere den Bot-Token

### 3. Environment-Variablen konfigurieren

Kopiere `.env.example` zu `.env`:

```bash
copy .env.example .env
```

Fülle die `.env` mit deinen Daten:

```env
TELEGRAM_BOT_TOKEN=dein_bot_token_hier
OPENAI_API_KEY=dein_openai_key_hier
ADMIN_USER_IDS=deine_telegram_user_id
```

**Deine Telegram User-ID finden:**
- Sende eine Nachricht an `@userinfobot`
- Kopiere deine User-ID

### 4. Bot starten

```bash
python main.py
```

## 📁 Projekt-Struktur

```
bot/
├── main.py                  # Bot Entry Point
├── config.py                # Konfiguration
├── requirements.txt         
├── .env                     # Environment-Variablen (nicht im Git!)
├── handlers/                # Command-Handler
│   ├── start.py            # /start Command
│   └── help.py             # /help Command
├── services/                
│   ├── logger.py           # Logging-System
│   └── template_manager.py # Message-Templates
├── templates/               # Jinja2-Templates
│   ├── welcome.txt         # Begrüßungstext
│   ├── help.txt            # Hilfetext
│   └── points.txt          # Punkte-Übersicht
├── photos/                  # Foto-Speicherung (gitignored)
└── logs/                    # Log-Dateien (gitignored)
```

## ✅ Status: Phase 1 - Abgeschlossen

- ✅ Projekt-Struktur erstellt
- ✅ Logging-System implementiert (3 Log-Dateien)
- ✅ Config-Management aufgesetzt
- ✅ Template-System eingerichtet (Jinja2)
- ✅ `/start` Command mit Begrüßungstext
- ✅ `/help` Command mit Spielregeln
- ✅ Admin-System vorbereitet

## 🎮 Bot-Commands (aktuell)

- `/start` - Begrüßung und Einführung in die Story
- `/help` - Detaillierte Spielregeln

## 📝 Nächste Schritte (Phase 2)

- [ ] Datenbank-Setup (SQLAlchemy Models)
- [ ] User-Registrierung in DB
- [ ] Foto-Upload Handler
- [ ] Lokale Foto-Speicherung
- [ ] `/punkte` Command

## 🔧 Development

### Logs ansehen

Logs befinden sich in `logs/`:
- `bot.log` - Alle Bot-Events
- `ai_evaluations.log` - KI-Bewertungen
- `errors.log` - Nur Fehler

### Admin-Funktionen

Admins werden in `.env` über `ADMIN_USER_IDS` definiert.

## 📄 Dokumentation

Siehe `REQUIREMENTS.md` für vollständige Anforderungen und Spezifikationen.
