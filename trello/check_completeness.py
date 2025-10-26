"""
Test-Script um die Vollständigkeit der Universen zu prüfen
"""
import sys
sys.path.insert(0, '.')

from markdown_parser import MarkdownParser

# Parse Universen
parser = MarkdownParser('../notes/Universen.md')
universes = parser.parse()

print("📊 Vollständigkeits-Check:\n")
print("=" * 70)

for universe in universes:
    status_icon = "✅" if universe.is_complete() else "⚠️"
    label = "Fertig" if universe.is_complete() else "Todo"
    
    print(f"\n{status_icon} {universe.title} [{label}]")
    print(f"   Status: {universe.status}")
    
    # Details
    missing = []
    if len(universe.characters) < 2:
        missing.append(f"Charaktere ({len(universe.characters)}/2)")
    if len(universe.character_ids) < 2:
        missing.append(f"Charakter-IDs ({len(universe.character_ids)}/2)")
    if not universe.team_id:
        missing.append("Team-ID")
    if not universe.easter_egg:
        missing.append("Easter Egg")
    if not universe.film_clip:
        missing.append("Filmausschnitt")
    if not universe.puzzle_link:
        missing.append("Puzzle-Link")
    if len(universe.posters) == 0:
        missing.append("Plakate")
    
    if missing:
        print(f"   Fehlend: {', '.join(missing)}")
    else:
        print("   Alle Elemente vorhanden! ✓")

print("\n" + "=" * 70)

# Statistik
complete = sum(1 for u in universes if u.is_complete())
total = len(universes)
print(f"\n📈 Gesamt: {complete}/{total} fertig ({complete*100//total}%)")
