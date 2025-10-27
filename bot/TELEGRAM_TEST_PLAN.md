# 🤖 Telegram Bot Test-Plan: Halloween 2025

## 📋 Übersicht

**Test-Datum:** 27. Oktober 2025  
**Bot-Name:** Halloween Rebellion Bot  
**Umgebung:** Development/Production  
**Tester:** [Name eintragen]

---

## 🚀 Vorbereitung (5 Min)

### 1. Bot starten
```bash
cd /home/fk/Dokumente/Worksheets/Eigene/Halloween25/bot
python main.py
```

### 2. Checkliste vor Tests
- [ ] Bot läuft ohne Errors
- [ ] Database initialisiert (23 Teams geladen)
- [ ] Telegram Bot Token funktioniert
- [ ] Admin User-IDs konfiguriert
- [ ] Logs werden geschrieben

### 3. Test-Material vorbereiten
- [ ] 3-4 verschiedene Fotos bereit (Handy/Computer)
- [ ] Telegram App geöffnet
- [ ] Bot gefunden über @[bot_username]
- [ ] Stopuhr/Timer bereit

---

## 🎯 Kern-Tests (Reihenfolge wichtig!)

### Test 1: Erste Kontaktaufnahme (2 Min)
**Ziel:** Bot-Registrierung und Story

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 1.1 | Sende `/start` | Willkommensnachricht mit Jahr 2097 Story | ⬜ | |
| 1.2 | Prüfe Story | Erwähnt KI-Herrschaft, Simulation, Rebellion | ⬜ | |
| 1.3 | Prüfe Punkte-Erklärung | 3 Punktesysteme erklärt | ⬜ | |
| 1.4 | Admin-Check | Falls Admin: "🔧 Admin-Modus" Meldung | ⬜ | Nur für Admins |

**Notizen:**
```
Response-Zeit: _____ Sekunden
Fehler: ________________
```

---

### Test 2: Hilfe anfordern (1 Min)
**Ziel:** Spielregeln verstehen

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 2.1 | Sende `/help` | Vollständige Spielregeln | ⬜ | |
| 2.2 | Prüfe Punkte | 1P Partyfotos, 20P Filme, 25P Teams/Puzzle | ⬜ | |
| 2.3 | Prüfe Beispiele | Beispiele für "Film: Matrix" etc. | ⬜ | |

---

### Test 3: Punkte-Status (leer) (1 Min)
**Ziel:** Anfangszustand prüfen

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 3.1 | Sende `/punkte` | 0 Punkte, kein Team | ⬜ | |
| 3.2 | Prüfe Breakdown | 0 Partyfotos, 0 Filme, 0 Team | ⬜ | |
| 3.3 | Prüfe Ranking | "X von Y Spielern" | ⬜ | |

---

### Test 4: Party-Foto Upload (2 Min)
**Ziel:** Basis-Foto-Upload funktioniert

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 4.1 | Sende Foto **ohne** Caption | "+1 Punkt für dein Party-Foto!" | ⬜ | |
| 4.2 | Prüfe Speicherung | Foto in `photos/party/` gespeichert | ⬜ | Check Dateisystem |
| 4.3 | Prüfe Thumbnail | Thumbnail-Datei erstellt | ⬜ | _thumb.jpg |
| 4.4 | Response-Zeit | < 5 Sekunden Upload-Bestätigung | ⬜ | |

---

### Test 5: Team-Beitritt (3 Min)
**Ziel:** Team-System funktioniert

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 5.1 | Berechne Matrix Team-ID | Trinity: 246935, Neo: 233579 → **480514** | ⬜ | Wichtig! |
| 5.2 | Sende `/teamid 480514` | "Willkommen im Team Matrix!" | ⬜ | |
| 5.3 | Punkte-Check | "+25 Punkte für Team-Beitritt!" | ⬜ | |
| 5.4 | Puzzle-Link | Puzzle-Link wird gesendet | ⬜ | |
| 5.5 | Test Duplikat | Sende `/teamid 480514` erneut | ⬜ | Sollte "bereits Mitglied" sagen |

**Team-IDs zum Testen:**
- Matrix: **480514** (Trinity: 246935 + Neo: 233579)
- Terminator: **226215** (Sarah: 213642 + John: 012573)  
- Demolition Man: **417849** (Spartan: 037534 + Huxley: 380315)

---

### Test 6: Film-Referenz (3 Min)
**Ziel:** Film-Erkennung funktioniert

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 6.1 | Sende Foto mit Caption `Film: Matrix` | "Film erkannt: Matrix! +20 Punkte!" | ⬜ | |
| 6.2 | Prüfe Speicherung | Foto in `photos/films/Matrix/` | ⬜ | |
| 6.3 | Test Duplikat | Sende nochmal `Film: Matrix` | ⬜ | "bereits erkannt" |
| 6.4 | Test anderer Film | Sende `Film: Terminator` | ⬜ | +20 Punkte erneut |

**Verfügbare Filme:** Matrix, Terminator, "Demolition Man", "The Fifth Element", "V wie Vendetta", etc.

---

### Test 7: Puzzle-Lösung (2 Min)
**Ziel:** Puzzle-Screenshot-Upload

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 7.1 | Sende Foto mit Caption `Team: 480514` | "Puzzle gelöst! +25 Punkte!" | ⬜ | Nur wenn im Team |
| 7.2 | Prüfe Speicherung | Foto in `photos/puzzles/` | ⬜ | |
| 7.3 | Test Duplikat | Sende nochmal `Team: 480514` | ⬜ | "bereits gelöst" |

---

### Test 8: Punkte-Status (gefüllt) (1 Min)
**Ziel:** Korrekte Punkteberechnung

| Schritt | Aktion | Erwartetes Ergebnis | ✅/❌ | Bemerkung |
|---------|--------|-------------------|-------|-----------|
| 8.1 | Sende `/punkte` | **Gesamt: 71 Punkte** | ⬜ | 1+25+20+25 |
| 8.2 | Breakdown prüfen | 1 Partyfoto, 2 Filme, Team Matrix | ⬜ | |
| 8.3 | Ranking prüfen | Position aktualisiert | ⬜ | |

---

## ⚠️ Fehler-Tests (Optional - 5 Min)

### Test 9: Ungültige Eingaben

| Test | Aktion | Erwartetes Ergebnis | ✅/❌ |
|------|--------|-------------------|-------|
| 9.1 | `/teamid 999999` | "Team-ID nicht gefunden" | ⬜ |
| 9.2 | `/teamid ABC123` | "6 Ziffern erforderlich" | ⬜ |
| 9.3 | `Film: UnbekannterFilm` | Als Partyfoto behandelt (+1P) | ⬜ |
| 9.4 | Foto mit `Team: 480514` ohne Team | "Erst Team beitreten!" | ⬜ |

---

## 👨‍💻 Admin-Tests (Optional - nur für Admins)

### Test 10: Admin-Commands

| Test | Aktion | Erwartetes Ergebnis | ✅/❌ |
|------|--------|-------------------|-------|
| 10.1 | `/admin` | Admin-Menü erscheint | ⬜ |
| 10.2 | `/players` | Liste aller Spieler | ⬜ |
| 10.3 | `/teams` | Liste aller Teams | ⬜ |
| 10.4 | `/stats` | Gesamt-Statistiken | ⬜ |

---

## 📊 Test-Auswertung

### Erfolgreiche Tests
- [ ] Test 1: Registrierung
- [ ] Test 2: Hilfe  
- [ ] Test 3: Punkte (leer)
- [ ] Test 4: Party-Foto
- [ ] Test 5: Team-Beitritt
- [ ] Test 6: Film-Referenz
- [ ] Test 7: Puzzle-Lösung
- [ ] Test 8: Punkte (gefüllt)

**Erfolgsquote: ___/8 Tests (____%)**

### Gefundene Probleme
```
Problem 1: __________________________________
Schweregrad: Kritisch/Hoch/Mittel/Niedrig
Beschreibung: ________________________________

Problem 2: __________________________________
Schweregrad: Kritisch/Hoch/Mittel/Niedrig  
Beschreibung: ________________________________
```

### Performance-Messung
```
Response-Zeiten:
- /start: _______ Sek
- /help: _______ Sek  
- /punkte: _______ Sek
- Foto-Upload: _______ Sek
- Team-Beitritt: _______ Sek

Upload-Größen getestet:
- Kleines Foto (<1MB): _______ Sek
- Großes Foto (>5MB): _______ Sek
```

---

## 📸 Screenshot-Dokumentation

**Wichtige Screenshots machen von:**
- [ ] Willkommensnachricht nach `/start`
- [ ] Erfolgreiche Punkte-Vergabe 
- [ ] Team-Beitritt Bestätigung
- [ ] Finale Punkte-Übersicht
- [ ] Eventuelle Fehlermeldungen

---

## 🎯 Test-Fazit

### Status
- [ ] **ERFOLGREICH** - Bot bereit für Production
- [ ] **ERFOLGREICH mit Einschränkungen** - Kleinere Bugs
- [ ] **FEHLGESCHLAGEN** - Kritische Probleme gefunden

### Empfehlung
```
[Hier deine Einschätzung eintragen]

Bereit für Halloween-Party: JA/NEIN
Notwendige Anpassungen: ___________________
Geschätzte Behebungszeit: _________________
```

### Nächste Schritte
- [ ] Bugs beheben
- [ ] Weitere Tests mit mehreren Usern  
- [ ] OpenAI Vision API testen (Phase 3)
- [ ] Production-Deployment vorbereiten

---

**Test abgeschlossen am:** ________________  
**Tester:** ________________________________  
**Gesamtzeit:** ____________________________