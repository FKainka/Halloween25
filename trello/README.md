# Halloween25 Trello-Synchronisation

Dieses Tool ermöglicht die bidirektionale Synchronisation zwischen der `Universen.md` Markdown-Datei und Trello-Karten.

## Features

- ✅ **Markdown → YAML Konvertierung**: Exportiere strukturierte Daten aus Markdown
- ✅ **Trello-Integration**: Jedes Universum wird als Trello-Karte dargestellt
- ✅ **Bidirektionale Synchronisation**: 
  - `push`: Lokale Änderungen zu Trello hochladen
  - `pull`: Änderungen von Trello herunterladen
  - `sync`: Automatische bidirektionale Synchronisation
- ✅ **Statusverwaltung**: Universen werden in Listen organisiert
  - "Fertiggeplant" 
  - "In Planung"
  - "Potentiell"

## Installation

1. **Python-Abhängigkeiten installieren:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Konfiguration erstellen:**
   ```bash
   copy config.ini.example config.ini
   ```

3. **Trello API-Credentials eintragen:**
   - Öffne `config.ini` in einem Texteditor
   - Hole deinen API-Key: https://trello.com/app-key
   - Generiere ein Token (auf der gleichen Seite)
   - Finde deine Board-ID in der URL deines Trello-Boards
     - Beispiel: `https://trello.com/b/ABC123/halloween25` → Board-ID ist `ABC123`

## Verwendung

### Grundlegende Befehle

```bash
# Lokale Änderungen zu Trello hochladen
python main.py push

# Änderungen von Trello herunterladen
python main.py pull

# Bidirektionale Synchronisation
python main.py sync

# Markdown zu YAML exportieren
python main.py export

# YAML zu Markdown importieren
python main.py import
```

### Workflow-Beispiel

1. **Initial Setup** - Erstelle Karten auf Trello:
   ```bash
   python main.py push
   ```

2. **Änderungen auf Trello** - Synchronisiere zu Markdown:
   ```bash
   python main.py pull
   ```

3. **Lokale Änderungen** - Update Trello:
   ```bash
   python main.py push
   ```

4. **Regelmäßige Synchronisation**:
   ```bash
   python main.py sync
   ```

## Datenstruktur

Jedes Universum enthält:

- **Titel**: Name des Films/Universums
- **Status**: fertiggeplant / in_planung / potentiell
- **Charaktere**: Zwei Hauptcharaktere mit Namen und IDs
- **Team-ID**: Kombinierte ID aus beiden Charakter-IDs
- **Easter Egg**: Name, Beschreibung und Beispielbild
- **Links**: 
  - Filmausschnitt (YouTube)
  - Puzzle-Link (Jigsaw Planet)
  - Plakate (lokale Bilder)

## Trello-Karten-Format

Jede Karte enthält:

- **Titel**: Universum-Name
- **Beschreibung**: Formatierter Text mit allen Details
  - Charakterinformationen
  - Easter Egg Details
  - Links zu Filmausschnitt und Puzzle
  - Plakat-Verweise
- **Liste**: Entspricht dem Status (Fertiggeplant/In Planung/Potentiell)

## Dateien

- `main.py` - CLI-Tool für Synchronisation
- `models.py` - Datenmodelle
- `markdown_parser.py` - Markdown-Parser
- `yaml_converter.py` - YAML-Konverter
- `trello_client.py` - Trello API-Client
- `sync_manager.py` - Synchronisations-Manager
- `config.ini` - Konfigurationsdatei (nicht im Git!)
- `requirements.txt` - Python-Abhängigkeiten

## Hinweise

- Die `config.ini` sollte nicht ins Git committed werden (enthält API-Keys!)
- Plakate bleiben lokal und werden nicht zu Trello hochgeladen
- Bei Konflikten hat Trello bei `pull` und `sync` Vorrang
- Die YAML-Datei dient als Zwischenformat und Cache

## Troubleshooting

### "Konfigurationsdatei nicht gefunden"
→ Erstelle `config.ini` aus `config.ini.example`

### "API-Fehler" / "401 Unauthorized"
→ Überprüfe API-Key und Token in `config.ini`

### "Board-ID ungültig"
→ Stelle sicher, dass die Board-ID korrekt ist (aus der URL kopieren)

### Karten werden doppelt erstellt
→ Verwende `pull` statt `push` wenn Karten bereits auf Trello existieren

## Erweiterungen

Mögliche zukünftige Features:
- Automatische Synchronisation (Timer)
- Konfliktauflösung mit Merge-Strategie
- Attachment-Upload für Plakate
- Custom Fields für IDs
- Webhook-Integration

---

**Erstellt für das Halloween25 Projekt** 🎃
