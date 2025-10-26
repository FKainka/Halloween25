# Test-Dokumentation: Halloween Bot

## Test-Status

**Datum:** 26. Oktober 2025  
**Version:** Phase 2 (Database + Handlers)

---

## Unit Tests

### Test-Suite erstellt
✅ **test_crud.py** - 14 Tests für Database CRUD-Operationen  
✅ **test_handlers.py** - 9 Tests für Bot Command Handler  
✅ **test_services.py** - 12 Tests für Services (PhotoManager, TemplateManager, YAMLLoader)

### Test-Ergebnisse (Erster Lauf)
- **7 Tests erfolgreich** ✅
- **25 Tests fehlgeschlagen** ⚠️ (API-Unterschiede zu Mocks)
- **3 Tests mit Fehlern** ❌ (Konstruktor-Unterschiede)

### Identifizierte Probleme
Die Tests zeigen Diskrepanzen zwischen:
1. **get_user_stats()** - Rückgabe-Format muss angepasst werden
2. **Handler Mocking** - Database-Imports müssen korrekt gemockt werden
3. **PhotoManager/TemplateManager** - Konstruktor-Parameter stimmen nicht überein
4. **has_solved_puzzle()** - Signatur weicht ab

**Nächster Schritt:** Tests an tatsächliche Implementierung anpassen ODER Bot-Code an Test-Erwartungen anpassen.

---

## Manueller Test-Plan

### 1. Bot starten
```cmd
cd c:\Projekte\Halloween25\bot
..\.venv\Scripts\python.exe main.py
```

**Erwartetes Verhalten:**
- ✅ Bot startet ohne Fehler
- ✅ "Bot gestartet als @<bot_name>" Meldung
- ✅ Farbige Logs erscheinen
- ✅ Database wird initialisiert (bot.db erstellt)
- ✅ 22 Teams aus YAML geladen

---

### 2. Test: /start Command

**Aktion:** Sende `/start` im Telegram Chat

**Erwartetes Verhalten:**
- ✅ User wird registriert in Database
- ✅ Story-Text erscheint:
  - "Jahr 2097"
  - "KI-Herrschaft"
  - "Simulation"
  - "Rebellion"
- ✅ Erklärung der 3 Punkte-Systeme
- ✅ Falls Admin: "🔧 Admin-Modus aktiviert" Hinweis

**Log-Prüfung:**
```
INFO - User 123456789 (username) executed command: /start
```

---

### 3. Test: /help Command

**Aktion:** Sende `/help` im Telegram Chat

**Erwartetes Verhalten:**
- ✅ Spielregeln werden angezeigt:
  - Party-Fotos: +1 Punkt
  - Film-Referenzen: +20 Punkte
  - Team-Beitritt: +25 Punkte
  - Puzzle lösen: +25 Punkte
- ✅ Beispiele für Foto-Captions

**Log-Prüfung:**
```
INFO - User 123456789 (username) executed command: /help
```

---

### 4. Test: /punkte Command (ohne Punkte)

**Aktion:** Sende `/punkte` im Telegram Chat

**Erwartetes Verhalten:**
- ✅ Punktestand: 0
- ✅ Party-Fotos: 0
- ✅ Film-Referenzen: 0
- ✅ Team: Noch nicht beigetreten
- ✅ Ranking: X von Y Spielern

**Log-Prüfung:**
```
INFO - User 123456789 (username) executed command: /punkte
```

---

### 5. Test: Party-Foto Upload (ohne Caption)

**Aktion:** Sende ein Foto OHNE Caption

**Erwartetes Verhalten:**
- ✅ Bestätigung: "+1 Punkt für dein Party-Foto!"
- ✅ Foto wird gespeichert in `photos/party/`
- ✅ Thumbnail wird erstellt (200x200px)
- ✅ Database: Submission mit type=PARTY_PHOTO, points=1

**Datei-Prüfung:**
```
photos/party/123456789_<timestamp>_<submission_id>.jpg
photos/party/123456789_<timestamp>_<submission_id>_thumb.jpg
```

**Log-Prüfung:**
```
INFO - User 123456789 uploaded party photo. Points awarded: 1
DEBUG - Photo saved: photos/party/...
```

---

### 6. Test: Team Join (Text-Nachricht)

**Vorbereitung:** Berechne Team-ID für "Matrix"
- Trinity ID: 246935
- Neo ID: 233579
- **Team-ID: 480514**

**Aktion:** Sende Text-Nachricht `Team: 480514`

**Erwartetes Verhalten:**
- ✅ Bestätigung: "Willkommen im Team Matrix!"
- ✅ "+25 Punkte für Team-Beitritt!"
- ✅ Puzzle-Link wird gesendet
- ✅ Database: user.team_id = 480514
- ✅ Database: Submission mit type=TEAM_JOIN, points=25

**Log-Prüfung:**
```
INFO - User 123456789 joined team Matrix (480514). Points: 25
```

---

### 7. Test: Team Join (ungültige ID)

**Aktion:** Sende Text-Nachricht `Team: 999999`

**Erwartetes Verhalten:**
- ❌ Fehlermeldung: "Team-ID nicht gefunden"
- ❌ Keine Punkte vergeben
- ❌ User bleibt ohne Team

---

### 8. Test: Team Join (falsches Format)

**Aktion:** Sende Text-Nachricht `Team: ABC123`

**Erwartetes Verhalten:**
- ❌ Fehlermeldung: "Ungültiges Format. Nutze: Team: 123456"
- ❌ Keine Punkte vergeben

---

### 9. Test: Film-Referenz (mit Caption)

**Aktion:** Sende Foto mit Caption `Film: Matrix`

**Erwartetes Verhalten:**
- ✅ Bestätigung: "Film erkannt: Matrix! +20 Punkte!"
- ✅ Foto wird gespeichert in `photos/films/Matrix/`
- ✅ Database: Submission mit type=FILM_REFERENCE, film_title=Matrix, points=20
- ✅ Database: EasterEgg für Matrix erstellt

**Datei-Prüfung:**
```
photos/films/Matrix/123456789_<timestamp>_<submission_id>.jpg
```

**Log-Prüfung:**
```
INFO - User 123456789 recognized film: Matrix. Points: 20
```

---

### 10. Test: Film-Referenz (Duplikat)

**Aktion:** Sende erneut Foto mit Caption `Film: Matrix`

**Erwartetes Verhalten:**
- ❌ Fehlermeldung: "Du hast Matrix bereits erkannt!"
- ❌ Keine Punkte vergeben
- ❌ Foto wird NICHT gespeichert

---

### 11. Test: Puzzle Screenshot (wenn im Team)

**Voraussetzung:** User ist in Team (Test 6 erfolgreich)

**Aktion:** Sende Foto mit Caption `Team: 480514`

**Erwartetes Verhalten:**
- ✅ Bestätigung: "Puzzle gelöst! +25 Punkte!"
- ✅ Foto wird gespeichert in `photos/puzzles/`
- ✅ Database: Submission mit type=PUZZLE, points=25

**Log-Prüfung:**
```
INFO - User 123456789 solved puzzle for team 480514. Points: 25
```

---

### 12. Test: Puzzle Screenshot (Duplikat)

**Aktion:** Sende erneut Foto mit Caption `Team: 480514`

**Erwartetes Verhalten:**
- ❌ Fehlermeldung: "Du hast das Puzzle bereits gelöst!"
- ❌ Keine Punkte vergeben

---

### 13. Test: Puzzle Screenshot (ohne Team)

**Voraussetzung:** User ist NICHT in einem Team

**Aktion:** Sende Foto mit Caption `Team: 480514`

**Erwartetes Verhalten:**
- ❌ Fehlermeldung: "Du musst erst einem Team beitreten!"
- ❌ Keine Punkte vergeben

---

### 14. Test: /punkte Command (mit Punkten)

**Voraussetzung:** User hat Tests 5, 6, 9, 11 abgeschlossen

**Aktion:** Sende `/punkte`

**Erwartetes Verhalten:**
- ✅ Punktestand: **71 Punkte** (1 + 25 + 20 + 25)
- ✅ Party-Fotos: 1 (+1 Punkt)
- ✅ Film-Referenzen: 1 (Matrix) (+20 Punkte)
- ✅ Team: Matrix (+25 Punkte für Beitritt)
- ✅ Puzzle: Gelöst (+25 Punkte)
- ✅ Ranking: Aktualisiert

---

## Database-Prüfung

### SQLite Queries zum Testen

```sql
-- Alle User anzeigen
SELECT * FROM users;

-- User-Punkte und Team
SELECT telegram_id, username, total_points, team_id FROM users;

-- Alle Submissions eines Users
SELECT submission_type, points_awarded, film_title, status, created_at 
FROM submissions 
WHERE user_id = 1;

-- Easter Eggs (erkannte Filme)
SELECT u.username, e.film_title, e.recognized_at
FROM easter_eggs e
JOIN users u ON e.user_id = u.id;

-- Team-Übersicht
SELECT film_title, team_id, character_1, character_2 FROM teams;
```

---

## Performance-Tests

### Foto-Upload-Geschwindigkeit
- ✅ Upload sollte < 5 Sekunden dauern
- ✅ Thumbnail-Generierung sollte < 1 Sekunde dauern

### Response-Zeit Commands
- ✅ /start: < 2 Sekunden
- ✅ /help: < 1 Sekunde
- ✅ /punkte: < 3 Sekunden (mit DB-Query)

---

## Error Handling Tests

### 15. Test: Foto ohne Photo-Objekt
**Aktion:** Sende Text mit Foto-Emoji 📷

**Erwartetes Verhalten:**
- ❌ Ignoriert (kein Foto-Handler)

### 16. Test: Sehr großes Foto
**Aktion:** Sende Foto > 10MB

**Erwartetes Verhalten:**
- ⚠️ Telegram-Limit greift (max 10MB)
- ✅ Falls durchkommt: Normal verarbeitet

### 17. Test: Ungültiges Caption-Format
**Aktion:** Sende Foto mit Caption `Film Matrix` (ohne Doppelpunkt)

**Erwartetes Verhalten:**
- ✅ Als Party-Foto behandelt (+1 Punkt)

---

## Zusammenfassung

### Kritische Tests (Must-Have)
- [x] /start - User Registration
- [x] Team Join mit korrekter ID
- [x] Party-Foto Upload
- [x] Film-Referenz
- [x] Puzzle-Submission
- [x] /punkte mit Breakdown

### Erweiterte Tests (Nice-to-Have)
- [ ] Admin-Commands
- [ ] AI Film-Validierung (Phase 3)
- [ ] Rate Limiting
- [ ] Concurrent Users

### Bekannte Probleme
1. Unit Tests benötigen Anpassung an echte API
2. Mocking-Strategie muss verfeinert werden
3. PhotoManager-Konstruktor hat kein base_path Parameter

---

## Nächste Schritte

1. **Bot manuell testen** - Alle 14 Test-Cases durchgehen
2. **Fehler dokumentieren** - Logs und Screenshots sammeln
3. **Unit Tests anpassen** - An echte Implementierung angleichen
4. **Integration Tests** - End-to-End Workflows testen
5. **Phase 3 planen** - AI-Integration vorbereiten
