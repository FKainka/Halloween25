"""
Parser für die Universen.md Datei
"""
import re
from typing import List, Dict, Optional
from models import Universe, Character, EasterEgg


class MarkdownParser:
    """Parser für Universen.md"""
    
    def __init__(self, markdown_path: str):
        self.markdown_path = markdown_path
        
    def parse(self) -> List[Universe]:
        """Parst die Markdown-Datei und gibt alle Universen zurück"""
        with open(self.markdown_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        universes = []
        
        # Finde alle Abschnitte
        sections = {
            'fertiggeplant': self._extract_section(content, r'# Universen/Referenzen \(Fertiggeplant:.*?\):'),
            'in_planung': self._extract_section(content, r'# Universen/Referenzen \(Noch in Planung:.*?\):'),
            'potentiell': self._extract_section(content, r'# Weitere Potenzielle Filme/Referenzen')
        }
        
        for status, section_content in sections.items():
            if section_content:
                universes.extend(self._parse_section(section_content, status))
        
        return universes
    
    def _extract_section(self, content: str, pattern: str) -> Optional[str]:
        """Extrahiert einen Abschnitt aus dem Content"""
        match = re.search(pattern, content)
        if not match:
            return None
        
        start = match.end()
        
        # Finde das Ende (nächste H1-Überschrift oder Ende des Dokuments)
        next_section = re.search(r'\n#[^#]', content[start:])
        if next_section:
            end = start + next_section.start()
        else:
            end = len(content)
        
        return content[start:end]
    
    def _parse_section(self, section: str, status: str) -> List[Universe]:
        """Parst einen Abschnitt und gibt die Universen zurück"""
        universes = []
        
        # Teile nach H2-Überschriften (## Filmtitel)
        universe_blocks = re.split(r'\n##\s+', section)
        
        for block in universe_blocks:
            if not block.strip():
                continue
            
            universe = self._parse_universe_block(block, status)
            if universe:
                universes.append(universe)
        
        return universes
    
    def _parse_universe_block(self, block: str, status: str) -> Optional[Universe]:
        """Parst einen einzelnen Universum-Block"""
        lines = block.split('\n')
        if not lines:
            return None
        
        title = lines[0].strip()
        
        # Initialisiere Universe
        universe = Universe(title=title, status=status)
        
        # Parse Charaktere
        characters_match = re.search(r'\*\*Charaktere:\*\*\s*(.*?)(?=\n\s*-\s*\*\*|$)', block, re.DOTALL)
        if characters_match:
            char_text = characters_match.group(1)
            # Extrahiere Namen
            char_names = re.findall(r'-\s*([^,\n]+(?:,\s*[^,\n]+)?)', char_text)
            if char_names:
                names = [n.strip() for n in char_names[0].split(',')]
                universe.characters = [Character(name=name.strip()) for name in names if name.strip()]
            
            # Extrahiere IDs
            ids_match = re.search(r'IDs:\s*([\d,\s]+)', char_text)
            if ids_match:
                ids = [id.strip() for id in ids_match.group(1).split(',')]
                universe.character_ids = ids
                # Weise IDs den Charakteren zu
                for i, char in enumerate(universe.characters):
                    if i < len(ids):
                        char.character_id = ids[i]
            
            # Extrahiere TeamID
            team_id_match = re.search(r'TeamID:\s*(\d+)', char_text)
            if team_id_match:
                universe.team_id = team_id_match.group(1)
        
        # Parse Easter Egg
        easter_egg_match = re.search(r'\*\*Easter Egg:\*\*\s*(.+?)(?=\n\s*-\s*\*\*Beschreibung|$)', block)
        if easter_egg_match:
            egg_name = easter_egg_match.group(1).strip()
            
            # Beschreibung
            desc_match = re.search(r'\*\*Beschreibung:\*\*\s*(.+?)(?=\n\s*-\s*\*\*|\n\s*\*\*|$)', block, re.DOTALL)
            description = desc_match.group(1).strip() if desc_match else ""
            
            # Beispielbild
            image_match = re.search(r'\*\*Beispielbild:\*\*\s*!\[.*?\]\((https?://[^\)]+)\)', block)
            example_image = image_match.group(1) if image_match else None
            
            universe.easter_egg = EasterEgg(
                name=egg_name,
                description=description,
                example_image=example_image
            )
        
        # Parse Filmausschnitt
        clip_match = re.search(r'\*\*Filmausschnitt:\*\*\s*\[.*?\]\((https?://[^\)]+)\)', block)
        if clip_match:
            universe.film_clip = clip_match.group(1)
        
        # Parse Puzzle Link
        puzzle_match = re.search(r'\*\*Puzzle Link:\*\*\s*\[.*?\]\((https?://[^\)]+)\)', block)
        if puzzle_match:
            universe.puzzle_link = puzzle_match.group(1)
        
        # Parse Plakate
        poster_matches = re.findall(r'!\[.*?\]\((bilder/[^\)]+)\)', block)
        universe.posters = poster_matches
        
        return universe
    
    def universes_to_markdown(self, universes: List[Universe]) -> str:
        """Konvertiert Universen zurück in Markdown-Format"""
        sections = {
            'fertiggeplant': [],
            'in_planung': [],
            'potentiell': []
        }
        
        # Gruppiere nach Status
        for universe in universes:
            sections[universe.status].append(universe)
        
        # Baue Markdown auf
        md_parts = []
        
        # Header mit Notizen bleibt gleich (kann separat gespeichert werden)
        md_parts.append("# Notizen:")
        md_parts.append("- Es gibt 15 Filme bzw. Referenzen.")
        md_parts.append("- Jeder Film enthält ein Easter Egg, einen Filmausschnitt, ein Plakat und einen Puzzle-Link.")
        md_parts.append("- Puzzle-Links stammen meist von Jigsaw Planet und sind auf 24–25 Teile begrenzt (wählbar).")
        md_parts.append("- Filmausschnitte sind überwiegend von YouTube und möglichst kurz gehalten (max. 2–3 Minuten).")
        md_parts.append("- Plakate werden aus dem Internet (Google Bildersuche, hohe Auflösung!) bezogen. Der Filmtitel sollte, wenn möglich, entfernt oder beschnitten werden.")
        md_parts.append("- Easter Eggs: Sie sollen leicht erkennbar, gut sichtbar und möglichst in einer Szene platziert sein, die an den jeweiligen Film erinnert. Dazu gibt es eine Beschreibung und – wenn möglich – ein Beispielbild (Google Bildersuche).")
        md_parts.append("- Charaktere: Zwei Hauptcharaktere mit Namen. Jeder Charakter erhält eine sechsstellige ID. Die TeamID ist ebenfalls sechsstellige und ergibt sich aus der Summe der einzelnen Charakter-IDs.")
        md_parts.append("\n\n---\n")
        
        # Fertiggeplante Universen
        if sections['fertiggeplant']:
            md_parts.append(f"\n# Universen/Referenzen (Fertiggeplant: {len(sections['fertiggeplant'])}):\n")
            for universe in sections['fertiggeplant']:
                md_parts.append(self._universe_to_markdown(universe))
        
        # In Planung
        if sections['in_planung']:
            md_parts.append(f"\n----\n\n# Universen/Referenzen (Noch in Planung: {len(sections['in_planung'])}):\n")
            for universe in sections['in_planung']:
                md_parts.append(self._universe_to_markdown(universe))
        
        # Potentielle
        if sections['potentiell']:
            md_parts.append(f"\n----\n\n# Weitere Potenzielle Filme/Referenzen ({len(sections['potentiell'])}):\n")
            for universe in sections['potentiell']:
                md_parts.append(self._universe_to_markdown(universe))
        
        return '\n'.join(md_parts)
    
    def _universe_to_markdown(self, universe: Universe) -> str:
        """Konvertiert ein einzelnes Universum zu Markdown"""
        parts = [f"\n## {universe.title}"]
        
        # Charaktere
        if universe.characters:
            parts.append("- **Charaktere:**")
            char_names = ', '.join([c.name for c in universe.characters])
            parts.append(f"  - {char_names}")
            
            if universe.character_ids:
                parts.append(f"  - IDs: {', '.join(universe.character_ids)}")
            
            if universe.team_id:
                parts.append(f"  - TeamID: {universe.team_id}")
        
        # Easter Egg
        if universe.easter_egg:
            parts.append(f"- **Easter Egg:** {universe.easter_egg.name}")
            if universe.easter_egg.description:
                parts.append(f"  - **Beschreibung:** {universe.easter_egg.description}")
            if universe.easter_egg.example_image:
                parts.append(f"  - **Beispielbild:** ![{universe.easter_egg.name}]({universe.easter_egg.example_image})")
        
        # Filmausschnitt
        if universe.film_clip:
            parts.append(f"- **Filmausschnitt:** [{universe.title} Szene]({universe.film_clip})")
        
        # Puzzle Link
        if universe.puzzle_link:
            parts.append(f"- **Puzzle Link:** [{universe.title} Puzzle Link]({universe.puzzle_link})")
        
        # Plakate
        if universe.posters:
            parts.append("- **Plakate:**")
            for poster in universe.posters:
                parts.append(f"  - ![{universe.title}]({poster})")
        
        return '\n'.join(parts)
