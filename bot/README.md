# Halloween 2025 - Rebellion Bot

Telegram-Bot für die Halloween-Party 2025: "Rebellion gegen die KI"

## 🚀 Setup

### Empfohlen: Docker Setup (einfach & isoliert)

```bash
# 1. Environment-Variablen konfigurieren
cp .env.example .env
nano .env  # Trage TELEGRAM_BOT_TOKEN und OPENAI_API_KEY ein

# 2. Bot starten
docker-compose up -d

# 3. Logs anzeigen
docker-compose logs -f
```

**Oder mit Makefile (noch einfacher):**
```bash
make setup   # .env erstellen
make up      # Bot starten
make logs    # Logs anzeigen
make help    # Alle Befehle anzeigen
```

📖 **Ausführliche Docker-Dokumentation:** siehe [DOCKER.md](DOCKER.md)

---

### Alternative: Manuelle Installation

#### 1. Dependencies installieren

```bash
pip install -r requirements.txt
```

#### 2. Bot bei BotFather registrieren

1. Öffne Telegram und suche nach `@BotFather`
2. Sende `/newbot`
3. Folge den Anweisungen und wähle einen Namen
4. Kopiere den Bot-Token

#### 3. Environment-Variablen konfigurieren

Kopiere `.env.example` zu `.env`:

```bash
cp .env.example .env
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

#### 4. Bot starten

```bash
python3 main.py
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

## 🎮 Bot-Commands

### User-Commands
- `/start` - Begrüßung und Einführung in die Story (zeigt Custom Keyboard)
- `/help` - Detaillierte Spielregeln und Anleitung
- `/punkte` - Aktuellen Punktestand und Breakdown anzeigen
- `/team <Team-ID>` - Einem Team beitreten (z.B. `/team 480514`)
- `/film <Filmtitel>` - Film-Referenz mit Foto einreichen (z.B. `/film Matrix`)
- `/puzzle` - Puzzle-Screenshot einreichen (benötigt Team-Mitgliedschaft)

### Custom Keyboard Buttons
Nach `/start` erhältst du ein permanentes Menü mit folgenden Buttons:
- **📸 Partyfoto** - Allgemeines Partyfoto hochladen (1 Punkt)
- **🎬 Film-Referenz** - Film-Referenz mit /film Command einreichen
- **👥 Team beitreten** - Mit /team Command einem Team beitreten
- **🧩 Puzzle lösen** - Puzzle-Screenshot mit /puzzle einreichen
- **🏆 Meine Punkte** - Punktestand abfragen
- **❓ Hilfe** - Spielregeln anzeigen

### Admin-Commands
- `/admin` - Admin-Dashboard
- `/players` - Alle Spieler anzeigen
- `/teams` - Team-Übersicht
- `/stats` - Party-Statistiken
- `/eastereggs` - Erkannte Film-Referenzen
- `/points <user_id> <punkte> <grund>` - Punkte manuell anpassen

## 📋 Foto-Upload Workflows

### 1️⃣ Allgemeines Partyfoto (1 Punkt)
- Einfach Foto senden (ohne Command)
- ODER Button "📸 Partyfoto" nutzen
- Automatisch 1 Punkt

### 2️⃣ Film-Referenz einreichen (20 Punkte bei Erfolg)
```
1. Foto mit Film-Referenz aufnehmen
2. Foto mit Caption senden: /film Matrix
3. KI analysiert das Foto (ca. 10 Sekunden)
4. Bei Erfolg: +20 Punkte
```

### 3️⃣ Team beitreten (25 Punkte)
```
1. QR-Code oder Team-IDs erhalten
2. Command senden: /team 480514
3. Automatisch +25 Punkte + Puzzle-Link
```

### 4️⃣ Puzzle lösen (25 Punkte)
```
1. Zuerst einem Team beitreten
2. Puzzle lösen (Link vom Bot)
3. Screenshot machen
4. Screenshot mit Command senden: /puzzle
5. Automatisch +25 Punkte
```

## 🔧 BotFather Setup

Um die Commands im Telegram-Client sichtbar zu machen, konfiguriere sie bei @BotFather:

```
/setcommands

start - Bot starten und Menü anzeigen
help - Spielregeln und Hilfe
punkte - Punktestand abfragen
team - Team beitreten (Team-ID erforderlich)
film - Film-Referenz einreichen (mit Foto)
puzzle - Puzzle-Screenshot einreichen
admin - Admin-Dashboard (nur für Admins)
```

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
