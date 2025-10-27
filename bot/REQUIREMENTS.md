# Anforderungsdokument: Halloween Party Telegram Bot

**Projektname:** Halloween 2025 - Rebellion Bot  
**Datum:** 26. Oktober 2025  
**Version:** 1.0  
**Party-Datum:** 31. Oktober 2025

---

## 1. Projekt-Übersicht

### 1.1 Kontext
Die Halloween-Party 2025 steht unter dem Motto "Rebellion gegen die KI". Gäste befinden sich in einer dystopischen Simulation (Jahr 2097), in der verschiedene Sci-Fi-Universen kollidieren. Der Telegram-Bot fungiert als "Widerstandskontakt" und ermöglicht es den Gästen, durch verschiedene Aufgaben Punkte zu sammeln und Teil der Rebellion zu werden.

### 1.2 Ziel
Entwicklung eines interaktiven Telegram-Bots, der:
- Gäste in die Story einführt
- Foto-Challenges verwaltet
- Ein Team-basiertes Puzzle-System ermöglicht
- Punkte automatisch vergibt und trackt
- Admin-Funktionen für Party-Organisation bietet

---

## 2. Funktionale Anforderungen

### 2.1 Spieler-Funktionen

#### 2.1.1 Begrüßung & Onboarding
**Anforderung:** `FR-01`
- **Beschreibung:** Beim ersten Kontakt (`/start`) erhält der User einen immersiven Begrüßungstext
- **Story-Text:** Siehe `notes/Begrüßung.md`
- **Verhalten:**
  - User wird in Datenbank registriert
  - Story-Text wird angezeigt (Jahr 2097, KI-Herrschaft, Simulation, Rebellion)
  - Erklärung der drei Punkte-Systeme
  - Bot erklärt seine Rolle als "freundlicher Helfer"

#### 2.1.2 Hilfe-System
**Anforderung:** `FR-02`
- **Beschreibung:** `/help` Command oder Custom Keyboard Button "❓ Hilfe"
- **Inhalt:**
  - Detaillierte Spielregeln
  - Erklärung aller Foto-Challenge-Typen
  - Punktesystem-Übersicht
  - Beispiele für korrekte Foto-Submissions
  - Kontakt bei Problemen

#### 2.1.3 Custom Keyboard Navigation
**Anforderung:** `FR-02b` (NEU)
- **Beschreibung:** Permanentes Custom Keyboard für einfache Navigation
- **Buttons:**
  - 📸 Partyfoto - Foto ohne Kategorie hochladen
  - 🎬 Film-Referenz - Hinweis zum /film Command
  - 👥 Team beitreten - Hinweis zum /team Command
  - 🧩 Puzzle lösen - Hinweis zum /puzzle Command
  - 🏆 Meine Punkte - Punktestand abfragen
  - ❓ Hilfe - Spielregeln anzeigen
- **Verhalten:**
  - Erscheint nach /start automatisch
  - Bleibt permanent sichtbar unter Chat-Eingabe
  - Buttons sind selbsterklärend und intuitiv

#### 2.1.4 Foto-Upload: Allgemeine Partyfotos
**Anforderung:** `FR-03`
- **Beschreibung:** User kann jederzeit Partyfotos ohne Command hochladen
- **Verhalten:**
  - Foto wird empfangen (ohne Caption oder mit beliebiger Caption)
  - User erhält **1 Punkt** automatisch
  - Bestätigungsnachricht: "Danke für das Partyfoto! +1 Punkt"
  - Foto wird in DB gespeichert mit Timestamp
- **Alternative:** Button "📸 Partyfoto" nutzen

#### 2.1.5 Foto-Upload: Film-Referenzen (NEU: Command-basiert)
**Anforderung:** `FR-04`
- **Beschreibung:** User sendet Foto mit `/film <Filmtitel>` Command
- **Usage:**
  - Foto auswählen
  - Als Caption eingeben: `/film Matrix`
  - Senden
- **Verhalten:**
  - Foto wird mit KI (OpenAI Vision API) analysiert
  - KI prüft, ob Foto eine Referenz zum genannten Film zeigt
  - Bei Erfolg: **20 Punkte** + Bestätigungsnachricht
  - Bei Ablehnung: Feedback-Nachricht mit Grund
  - System prüft, ob User diesen Film bereits submitted hat (Easter Egg Tracking)
  - Gleicher Film kann nur 1x pro User punkten
- **Vorteile gegenüber Caption-Parsing:**
  - ✅ Autocomplete im Telegram-Client
  - ✅ Weniger fehleranfällig
  - ✅ Klare Syntax
  - ✅ Command erscheint in /help

**Film-Katalog:** 22 Filme aus `notes/universen.yaml`:
- Matrix, Demolition Man, Terminator, The Fifth Element, V wie Vendetta
- Blade Runner, Gattaca, In Time, Wanted, Ex Machina
- Starship Troopers, Equilibrium, Robocop, I Robot, Mad Max
- 2001 Odyssee im Weltraum, Her, Transcendence, 1984
- Maze Runner, Die Insel, Genesis Backup (Admin-Only)

#### 2.1.6 Team-Bildung via Command
**Anforderung:** `FR-05`
- **Beschreibung:** User sendet `/team <6-stellige Team-ID>`
- **Team-IDs:** 22 Teams basierend auf Film-Charakteren (siehe `universen.yaml`)
- **Verhalten:**
  - Bot validiert Team-ID gegen Liste
  - Bei gültiger ID: User wird Team zugeordnet
  - User erhält **25 Punkte**
  - Bot sendet Bestätigungsnachricht mit Puzzle-Link
  - User kann nur 1 Team beitreten
- **Usage:** `/team 480514`

**Beispiel Team-IDs:**
- Matrix: `480514` (Trinity + Neo)
- Terminator: `226215` (Sarah + John)
- Wanted: `816312` (Wesley + Fox)
- usw. (alle 22 Teams aus YAML)

#### 2.1.7 Puzzle-Lösung (NEU: Command-basiert)
**Anforderung:** `FR-06`
- **Beschreibung:** User sendet Screenshot mit `/puzzle` Command
- **Usage:**
  - Puzzle lösen (Link vom Bot nach Team-Beitritt)
  - Screenshot machen
  - Screenshot mit Caption `/puzzle` senden
- **Verhalten:**
  - Bot empfängt Screenshot
  - Prüft, ob User bereits Team-Member ist
  - Prüft, ob User bereits Puzzle-Punkte erhalten hat
  - Bei Erfolg: **25 Punkte** + Glückwunsch-Nachricht
  - Nur 1x pro User möglich
- **Vorteile:**
  - ✅ Keine Team-ID mehr nötig (wird aus User-Profil gelesen)
  - ✅ Einfachere Eingabe
  - ✅ Klarer Command-Name

#### 2.1.8 Punktestand abfragen
**Anforderung:** `FR-07`
- **Beschreibung:** `/punkte` Command oder Custom Keyboard Button "🏆 Meine Punkte"
- **Anzeige:**
  - Aktuelle Gesamtpunktzahl
  - Breakdown nach Kategorien:
    - Partyfotos: X × 1 = Y Punkte
    - Film-Referenzen: X × 20 = Y Punkte
    - Team-Beitritt: 25 Punkte (oder 0)
    - Puzzle gelöst: 25 Punkte (oder 0)
  - Ranking-Position (optional)
  - Welche Filme bereits erkannt wurden

---

### 2.2 Admin-Funktionen

#### 2.2.1 Admin-Authentifizierung
**Anforderung:** `FR-08`
- **Beschreibung:** Nur autorisierte User haben Admin-Zugriff
- **Methode:** Whitelist von Telegram User-IDs in `.env`
- **Verhalten:**
  - Admin-Commands nur für autorisierte User sichtbar
  - Bei unauthorisiertem Zugriff: Fehlermeldung

#### 2.2.2 Spieler-Übersicht
**Anforderung:** `FR-09`
- **Beschreibung:** `/admin_players` zeigt alle registrierten Spieler
- **Anzeige:**
  - Liste aller User (Name, Username, User-ID)
  - Aktuelle Punktzahl
  - Team-Zugehörigkeit
  - Anzahl Submissions pro Kategorie
  - Registrierungs-Zeitpunkt

#### 2.2.3 Punkte manuell anpassen
**Anforderung:** `FR-10`
- **Beschreibung:** `/admin_points <user_id> <punkte> <grund>`
- **Verhalten:**
  - Admin kann Punkte hinzufügen oder abziehen
  - Grund wird im Log gespeichert
  - User erhält Benachrichtigung über Änderung

#### 2.2.4 Team-Übersicht
**Anforderung:** `FR-11`
- **Beschreibung:** `/admin_teams` zeigt alle Teams
- **Anzeige:**
  - Team-ID, Film-Titel
  - Anzahl Mitglieder
  - Durchschnittliche Punkte
  - Welche User sind im Team

#### 2.2.5 Easter Egg Tracking
**Anforderung:** `FR-12`
- **Beschreibung:** `/admin_eastereggs` zeigt erkannte Film-Referenzen
- **Anzeige:**
  - Liste aller 22 Filme
  - Wie oft wurde jeder Film erkannt
  - Von welchen Usern
  - Erfolgsquote der KI-Bewertung

#### 2.2.6 Statistiken
**Anforderung:** `FR-13`
- **Beschreibung:** `/admin_stats` zeigt Party-Statistiken
- **Anzeige:**
  - Gesamtanzahl User
  - Gesamtanzahl Fotos
  - Durchschnittliche Punkte
  - Aktivste User (Top 10)
  - Beliebteste Film-Referenzen
  - Zeitlicher Verlauf (Foto-Uploads pro Stunde)

---

## 3. Nicht-Funktionale Anforderungen

### 3.1 Performance
**Anforderung:** `NFR-01`
- Bot muss Foto-Uploads innerhalb von **5 Sekunden** verarbeiten
- KI-Bewertung sollte maximal **10 Sekunden** dauern
- Datenbank-Queries unter **1 Sekunde**

### 3.2 Verfügbarkeit
**Anforderung:** `NFR-02`
- Bot muss am 31.10.2025 von 18:00 bis 04:00 Uhr verfügbar sein
- Ausfallzeit < 5 Minuten während Party
- Automatisches Restart bei Crash

### 3.3 Skalierbarkeit
**Anforderung:** `NFR-03`
- Bot muss **30 gleichzeitige User** unterstützen
- Foto-Queue-System bei hoher Last
- Datenbank sollte 1000+ Fotos ohne Slowdown speichern

### 3.4 Sicherheit
**Anforderung:** `NFR-04`
- API-Keys in `.env` (nicht im Git)
- Admin-Funktionen nur für autorisierte User
- SQL-Injection-Prevention durch SQLAlchemy ORM
- Rate-Limiting gegen Spam (max. 10 Fotos/Minute pro User)

### 3.5 Usability
**Anforderung:** `NFR-05`
- Intuitive Bot-Befehle mit Custom Keyboard (ReplyKeyboardMarkup)
- Command-basiertes System für Film und Puzzle (statt fehleranfällige Captions)
- Klare Fehlermeldungen mit Beispielen
- Feedback bei jeder Aktion
- Story-basierte, freundliche Bot-Persönlichkeit
- Permanentes Menü für wichtigste Funktionen
- Autocomplete-Unterstützung durch Telegram Commands

### 3.6 Wartbarkeit
**Anforderung:** `NFR-06`
- Modulare Code-Struktur
- Logging aller wichtigen Events
- Einfache Konfiguration via `.env`
- Dokumentation im Code

### 3.7 Logging & Monitoring
**Anforderung:** `NFR-07`
- **Strukturiertes Logging:** Alle Events mit Timestamp, User-ID, Action
- **Log-Levels:** DEBUG, INFO, WARNING, ERROR, CRITICAL
- **Separate Log-Dateien:**
  - `bot.log` - Alle Bot-Events
  - `ai_evaluations.log` - KI-Bewertungen mit Details
  - `errors.log` - Nur Fehler und Exceptions
- **Rotation:** Log-Dateien rotieren täglich, behalten letzte 7 Tage
- **Console Output:** Wichtige Events auch in Console für Live-Monitoring

### 3.8 Nachrichten-Template-System
**Anforderung:** `NFR-08`
- **Template-Engine:** Jinja2 für alle Bot-Nachrichten
- **Mehrsprachigkeit:** Vorbereitung für DE/EN (aktuell nur DE)
- **Zentrale Templates:** Alle Texte in separaten Template-Dateien
- **Variablen-Support:** Dynamische Inhalte (Namen, Punkte, Filme)
- **Einfache Bearbeitung:** Nicht-Programmierer können Texte anpassen

### 3.9 Foto-Speicherung
**Anforderung:** `NFR-09`
- **Lokale Speicherung:** Alle Fotos werden lokal gespeichert
- **Dateistruktur:**
  - `photos/party/` - Allgemeine Partyfotos
  - `photos/films/` - Film-Referenzen (unterteilt nach Film)
  - `photos/puzzles/` - Puzzle-Screenshots
- **Dateinamen-Format:** `{user_id}_{timestamp}_{submission_id}.jpg`
- **Datenbank-Referenz:** DB speichert nur Dateipfad, nicht Binärdaten
- **Thumbnail-Generierung:** Automatische Thumbnails (200x200px) für Admin-Panel
- **Backup:** Fotos werden zusätzlich täglich gesichert

---

## 4. Daten-Modell

### 4.1 Datenbank-Schema

#### Tabelle: `users`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | INTEGER | Primary Key |
| `telegram_id` | BIGINT | Telegram User-ID (unique) |
| `username` | VARCHAR | Telegram Username |
| `first_name` | VARCHAR | Vorname |
| `last_name` | VARCHAR | Nachname |
| `team_id` | VARCHAR(6) | Foreign Key zu teams (nullable) |
| `total_points` | INTEGER | Gesamtpunktzahl |
| `created_at` | DATETIME | Registrierungszeitpunkt |
| `is_admin` | BOOLEAN | Admin-Flag |

#### Tabelle: `teams`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | INTEGER | Primary Key |
| `team_id` | VARCHAR(6) | 6-stellige Team-ID (unique) |
| `film_title` | VARCHAR | Film-Titel |
| `character_1` | VARCHAR | Charakter 1 Name |
| `character_2` | VARCHAR | Charakter 2 Name |
| `puzzle_link` | VARCHAR | URL zum Puzzle |
| `created_at` | DATETIME | Erstellungszeitpunkt |

#### Tabelle: `submissions`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | INTEGER | Primary Key |
| `user_id` | INTEGER | Foreign Key zu users |
| `submission_type` | ENUM | `party_photo`, `film_reference`, `team_join`, `puzzle` |
| `photo_file_id` | VARCHAR | Telegram File-ID |
| `photo_path` | VARCHAR | Lokaler Dateipfad |
| `thumbnail_path` | VARCHAR | Thumbnail Dateipfad |
| `caption` | TEXT | User-Caption |
| `film_title` | VARCHAR | Bei Film-Referenz: Film-Titel |
| `points_awarded` | INTEGER | Vergebene Punkte |
| `ai_evaluation` | TEXT | KI-Bewertung (JSON) |
| `status` | ENUM | `pending`, `approved`, `rejected` |
| `created_at` | DATETIME | Upload-Zeitpunkt |

#### Tabelle: `easter_eggs`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | INTEGER | Primary Key |
| `user_id` | INTEGER | Foreign Key zu users |
| `film_title` | VARCHAR | Film-Titel |
| `recognized_at` | DATETIME | Erkennungszeitpunkt |

#### Tabelle: `admin_logs`
| Feld | Typ | Beschreibung |
|------|-----|-------------|
| `id` | INTEGER | Primary Key |
| `admin_id` | INTEGER | Foreign Key zu users |
| `action` | VARCHAR | Admin-Aktion |
| `target_user_id` | INTEGER | Betroffener User |
| `details` | TEXT | Details (JSON) |
| `created_at` | DATETIME | Zeitpunkt |

---

## 5. KI-Integration

### 5.1 OpenAI Vision API
**Provider:** OpenAI GPT-4 Vision  
**Endpoint:** `https://api.openai.com/v1/chat/completions`

**Prompt-Template für Film-Bewertung:**
```
Du bist ein Experte für Sci-Fi-Filme. Analysiere das folgende Foto und bewerte, 
ob es eine erkennbare Referenz zum Film "{film_title}" zeigt.

Prüfe auf:
- Easter Eggs (spezifische Gegenstände aus dem Film)
- Nachgestellte Szenen
- Charaktere oder Kostüme
- Ikonische Requisiten oder Settings

Antworte in folgendem JSON-Format:
{
  "is_reference": true/false,
  "confidence": 0-100,
  "reasoning": "Kurze Erklärung",
  "detected_elements": ["Element 1", "Element 2"]
}
```

**Fallback:** Bei API-Fehler → Foto in Admin-Queue für manuelle Review

---

## 6. Technische Spezifikation

### 6.1 Tech-Stack
- **Sprache:** Python 3.11+
- **Bot-Framework:** `python-telegram-bot` v21.x
- **Datenbank:** SQLite (Development) / PostgreSQL (Production)
- **ORM:** SQLAlchemy 2.x
- **KI:** OpenAI API (GPT-4 Vision)
- **Config:** `python-dotenv`
- **Deployment:** Railway / Heroku / VPS

### 6.2 Dependencies (`requirements.txt`)
```
python-telegram-bot[all]==21.5
sqlalchemy==2.0.23
python-dotenv==1.0.0
openai==1.3.5
pillow==10.1.0
qrcode==7.4.2
pyyaml==6.0.1
alembic==1.12.1
jinja2==3.1.2
```

### 6.3 Umgebungsvariablen (`.env`)
```
# Bot Configuration
TELEGRAM_BOT_TOKEN=<bot_token>
OPENAI_API_KEY=<api_key>

# Database
DATABASE_URL=sqlite:///bot.db

# Admin
ADMIN_USER_IDS=123456789,987654321

# Environment
ENVIRONMENT=development
LOG_LEVEL=INFO

# File Storage
PHOTOS_BASE_PATH=./photos
LOGS_BASE_PATH=./logs

# AI Settings
AI_CONFIDENCE_THRESHOLD=70
AI_TIMEOUT_SECONDS=15
```

### 6.4 Template-System Details

**Template-Variablen (Beispiele):**

`templates/welcome.txt`:
```jinja2
Hallo {{ user_name }},

schön, dass wir dich gefunden haben. Lass mich dir zunächst erklären, wo du dich befindest...

[Vollständiger Text aus Begrüßung.md mit Variablen]
```

`templates/points.txt`:
```jinja2
🎯 Deine Rebellion-Punkte:

Gesamt: {{ total_points }} Punkte
{% if ranking %}Rang: {{ ranking }} von {{ total_users }}{% endif %}

📊 Breakdown:
🎉 Partyfotos: {{ party_photos_count }} × 1 = {{ party_points }} Punkte
🎬 Film-Referenzen: {{ film_count }} × 20 = {{ film_points }} Punkte
👥 Team-Beitritt: {{ team_points }} Punkte
🧩 Puzzle gelöst: {{ puzzle_points }} Punkte

{% if recognized_films %}
✅ Erkannte Filme:
{% for film in recognized_films %}  • {{ film }}
{% endfor %}
{% endif %}
```

`templates/film_approved.txt`:
```jinja2
🎬 Hervorragend, Reisender!

Deine Referenz zu "{{ film_title }}" wurde erkannt!

{{ ai_reasoning }}

+{{ points }} Punkte für die Rebellion!

Aktuelle Punkte: {{ total_points }}
```

### 6.5 Logging-Konfiguration

**Log-Format:**
```
[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s
```

**Beispiel-Logs:**
```
[2025-10-31 20:15:23] INFO [handlers.photo:45] User 123456789 uploaded party photo
[2025-10-31 20:15:28] INFO [services.ai_evaluator:78] Evaluating film reference: Matrix
[2025-10-31 20:15:35] INFO [services.ai_evaluator:92] AI approved with 85% confidence
[2025-10-31 20:15:36] INFO [services.points_manager:34] Awarded 20 points to user 123456789
[2025-10-31 20:16:02] ERROR [services.ai_evaluator:105] OpenAI API timeout after 15s
```

**Logger-Struktur:**
- `bot.main` - Hauptprozess-Events
- `bot.handlers` - Command-Handler
- `bot.services.ai` - KI-Bewertungen
- `bot.services.photos` - Foto-Verarbeitung
- `bot.database` - DB-Operationen

---

## 7. Projekt-Phasen & Zeitplan

### Phase 1: Setup & Grundgerüst (Tag 1)
- ✅ Projekt-Struktur erstellen
- ✅ Bot registrieren bei BotFather
- ✅ Dependencies installieren
- ✅ Datenbank-Schema definieren
- ✅ Logging-System einrichten
- ✅ Template-System aufsetzen
- ✅ Foto-Speicher-Struktur anlegen
- ✅ `/start` und `/help` Commands

### Phase 2: Basis-Funktionen (Tag 2)
- ✅ User-Registrierung
- ✅ Foto-Upload mit lokaler Speicherung
- ✅ Thumbnail-Generierung
- ✅ Punkte-System (basic)
- ✅ `/punkte` Command

### Phase 3: Team-System (Tag 3)
- ✅ Teams aus YAML laden
- ✅ QR-Code Generator
- ✅ Team-Beitritt-Logic
- ✅ Puzzle-Link Versand

### Phase 4: KI-Bewertung (Tag 4)
- ✅ OpenAI Integration
- ✅ Film-Referenz Parsing
- ✅ KI-Prompt Optimierung
- ✅ Easter Egg Tracking

### Phase 5: Admin-Panel (Tag 5)
- ✅ Admin-Commands
- ✅ Statistiken
- ✅ Manuelle Punkte-Verwaltung

### Phase 6: Testing & Polish (Tag 6-7)
- ✅ End-to-End Tests
- ✅ Error Handling
- ✅ Performance-Optimierung
- ✅ Deployment

### Phase 7: Go-Live (31.10.2025)
- ✅ Monitoring
- ✅ Live-Support

---

## 8. Offene Fragen & Entscheidungen

### 8.1 KI-Bewertung
- [ ] **Budget:** Wie viel OpenAI-Budget ist verfügbar? (~$0.01-0.03 pro Bild)
- [ ] **Fallback:** Sollen Fotos bei KI-Fehler automatisch genehmigt werden?
- [ ] **Threshold:** Ab welchem Confidence-Level (%) wird Foto akzeptiert? (Vorschlag: 70%)

### 8.2 Puzzle-Submission
- [ ] **Bewertung:** Screenshot automatisch akzeptieren oder manuell prüfen?
- [ ] **Nachweis:** Reicht Screenshot oder brauchen wir zusätzliche Validierung?

### 8.3 Allgemeine Partyfotos
- [ ] **Limit:** Maximale Anzahl pro User? (Vorschlag: 20)
- [ ] **Review:** Automatisch 1 Punkt oder Admin-Review?

### 8.4 Hosting
- [ ] **Platform:** Railway, Heroku, eigener VPS?
- [ ] **Datenbank:** SQLite oder PostgreSQL?
- [ ] **Kosten:** Budget für Hosting?

### 8.5 Admin-IDs
- [ ] **Wer:** Telegram User-IDs der Admins?
- [ ] **Anzahl:** Wie viele Admins werden benötigt?

### 8.6 QR-Codes
- [ ] **Format:** Physische QR-Codes ausdrucken oder digital?
- [ ] **Verteilung:** Wie bekommen Gäste ihre QR-Codes?

---

## 9. Risiken & Mitigation

| Risiko | Wahrscheinlichkeit | Impact | Mitigation |
|--------|-------------------|--------|------------|
| OpenAI API Down | Mittel | Hoch | Fallback auf manuelle Review-Queue |
| Bot-Server Crash | Niedrig | Kritisch | Auto-Restart, Health-Checks, Monitoring |
| Datenbank-Überlastung | Niedrig | Mittel | Connection Pooling, Indexierung |
| Spam-Angriffe | Mittel | Mittel | Rate-Limiting (10 Fotos/Min) |
| User verstehen Bot nicht | Hoch | Mittel | Ausführliche `/help`, Beispiele, Testing |
| KI gibt falsche Bewertungen | Mittel | Niedrig | Admin kann manuell übersteuern |

---

## 10. Success-Kriterien

### Must-Have (MVP)
- ✅ Bot ist während Party erreichbar
- ✅ User können Fotos hochladen
- ✅ Punkte-System funktioniert
- ✅ Team-Beitritt möglich
- ✅ Admin kann User/Punkte sehen

### Should-Have
- ✅ KI-Bewertung für Film-Referenzen
- ✅ Easter Egg Tracking (keine Duplikate)
- ✅ Ranking-System
- ✅ Statistiken

### Nice-to-Have
- ⚪ Leaderboard öffentlich im Bot
- ⚪ Foto-Galerie für alle User
- ⚪ Achievements/Badges
- ⚪ Push-Benachrichtigungen bei neuen Challenges

---

## 11. Kontakte & Ressourcen

**Projekt-Owner:** FKainka  
**Repository:** https://github.com/FKainka/Halloween25  
**Party-Datum:** 31. Oktober 2025  

**Externe Ressourcen:**
- Film-Daten: `notes/universen.yaml`
- Story-Text: `notes/Begrüßung.md`
- Trello-Integration: `trello/` (optional)

---

**Nächster Schritt:** Phase 1 Setup starten? 🚀
