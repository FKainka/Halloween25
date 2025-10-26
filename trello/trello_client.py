"""
Trello API-Integration für Halloween25
"""
import requests
from typing import List, Dict, Optional
from models import Universe


class TrelloClient:
    """Client für die Trello API"""
    
    BASE_URL = "https://api.trello.com/1"
    
    def __init__(self, api_key: str, api_token: str, board_id: str):
        self.api_key = api_key
        self.api_token = api_token
        self.board_id = board_id
        self.auth_params = {
            'key': self.api_key,
            'token': self.api_token
        }
    
    def _request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Führt eine API-Anfrage aus"""
        url = f"{self.BASE_URL}/{endpoint}"
        params = kwargs.get('params', {})
        params.update(self.auth_params)
        kwargs['params'] = params
        
        response = requests.request(method, url, **kwargs)
        response.raise_for_status()
        return response
    
    def get_lists(self) -> Dict[str, str]:
        """Holt alle Listen auf dem Board"""
        response = self._request('GET', f'boards/{self.board_id}/lists')
        lists = response.json()
        
        return {lst['name']: lst['id'] for lst in lists}
    
    def create_list(self, name: str) -> str:
        """Erstellt eine neue Liste auf dem Board"""
        response = self._request(
            'POST',
            'lists',
            params={'name': name, 'idBoard': self.board_id}
        )
        return response.json()['id']
    
    def get_or_create_list(self, name: str) -> str:
        """Holt oder erstellt eine Liste"""
        lists = self.get_lists()
        if name in lists:
            return lists[name]
        return self.create_list(name)
    
    def create_card(self, list_id: str, universe: Universe) -> str:
        """Erstellt eine Trello-Karte für ein Universum"""
        # Baue die Kartenbeschreibung auf
        description = self._build_card_description(universe)
        
        # Erstelle Custom Fields (Labels)
        labels = self._build_labels(universe)
        
        params = {
            'idList': list_id,
            'name': universe.title,
            'desc': description
        }
        
        response = self._request('POST', 'cards', params=params)
        card_id = response.json()['id']
        
        # Füge Labels hinzu (falls vorhanden)
        if labels:
            self._add_labels_to_card(card_id, labels)
        
        return card_id
    
    def update_card(self, card_id: str, universe: Universe) -> None:
        """Aktualisiert eine bestehende Trello-Karte"""
        description = self._build_card_description(universe)
        
        params = {
            'name': universe.title,
            'desc': description
        }
        
        self._request('PUT', f'cards/{card_id}', params=params)
    
    def get_cards(self, list_id: str) -> List[Dict]:
        """Holt alle Karten aus einer Liste"""
        response = self._request('GET', f'lists/{list_id}/cards')
        return response.json()
    
    def get_all_cards(self) -> List[Dict]:
        """Holt alle Karten vom Board"""
        response = self._request('GET', f'boards/{self.board_id}/cards')
        return response.json()
    
    def _build_card_description(self, universe: Universe) -> str:
        """Baut die Kartenbeschreibung auf"""
        parts = []
        
        # Charaktere
        if universe.characters:
            char_info = ', '.join([c.name for c in universe.characters])
            parts.append(f"**Charaktere:** {char_info}")
            
            if universe.character_ids:
                parts.append(f"**IDs:** {', '.join(universe.character_ids)}")
            
            if universe.team_id:
                parts.append(f"**Team-ID:** {universe.team_id}")
        
        parts.append("")  # Leerzeile
        
        # Easter Egg
        if universe.easter_egg:
            parts.append(f"**Easter Egg:** {universe.easter_egg.name}")
            if universe.easter_egg.description:
                parts.append(f"{universe.easter_egg.description}")
            if universe.easter_egg.example_image:
                parts.append(f"[Beispielbild]({universe.easter_egg.example_image})")
        
        parts.append("")  # Leerzeile
        
        # Links
        links = []
        if universe.film_clip:
            links.append(f"🎬 [Filmausschnitt]({universe.film_clip})")
        if universe.puzzle_link:
            links.append(f"🧩 [Puzzle]({universe.puzzle_link})")
        
        if links:
            parts.append("**Links:**")
            parts.extend(links)
        
        # Plakate
        if universe.posters:
            parts.append("")
            parts.append("**Plakate:**")
            for poster in universe.posters:
                parts.append(f"- {poster}")
        
        return '\n'.join(parts)
    
    def _build_labels(self, universe: Universe) -> List[str]:
        """Erstellt Labels für die Karte (Status als Label)"""
        labels = []
        if universe.status:
            labels.append(universe.status)
        return labels
    
    def _add_labels_to_card(self, card_id: str, labels: List[str]) -> None:
        """Fügt Labels zu einer Karte hinzu (vereinfacht)"""
        # Hinweis: Labels müssen normalerweise auf dem Board bereits existieren
        # Dies ist eine vereinfachte Version
        pass
    
    def parse_card_to_universe(self, card: Dict) -> Universe:
        """Konvertiert eine Trello-Karte zurück zu einem Universe-Objekt"""
        from models import Character, EasterEgg
        import re
        
        title = card['name']
        description = card['desc']
        
        # Extrahiere Informationen aus der Beschreibung
        universe = Universe(title=title, status='fertiggeplant')
        universe.trello_card_id = card['id']
        universe.trello_list_id = card['idList']
        
        # Parse Charaktere
        char_match = re.search(r'\*\*Charaktere:\*\*\s*(.+)', description)
        if char_match:
            char_names = [n.strip() for n in char_match.group(1).split(',')]
            universe.characters = [Character(name=name) for name in char_names]
        
        # Parse IDs
        ids_match = re.search(r'\*\*IDs:\*\*\s*([\d,\s]+)', description)
        if ids_match:
            universe.character_ids = [id.strip() for id in ids_match.group(1).split(',')]
        
        # Parse Team-ID
        team_id_match = re.search(r'\*\*Team-ID:\*\*\s*(\d+)', description)
        if team_id_match:
            universe.team_id = team_id_match.group(1)
        
        # Parse Easter Egg
        easter_egg_match = re.search(r'\*\*Easter Egg:\*\*\s*(.+?)(?=\n|$)', description)
        if easter_egg_match:
            egg_name = easter_egg_match.group(1).strip()
            
            # Beschreibung (nächste Zeile nach Easter Egg Name)
            desc_match = re.search(rf'\*\*Easter Egg:\*\*\s*{re.escape(egg_name)}\s*\n(.+?)(?=\n\[|\n\*\*|\n\n|$)', description, re.DOTALL)
            egg_description = desc_match.group(1).strip() if desc_match else ""
            
            # Beispielbild
            image_match = re.search(r'\[Beispielbild\]\((.+?)\)', description)
            example_image = image_match.group(1) if image_match else None
            
            universe.easter_egg = EasterEgg(
                name=egg_name,
                description=egg_description,
                example_image=example_image
            )
        
        # Parse Links
        clip_match = re.search(r'🎬 \[Filmausschnitt\]\((.+?)\)', description)
        if clip_match:
            universe.film_clip = clip_match.group(1)
        
        puzzle_match = re.search(r'🧩 \[Puzzle\]\((.+?)\)', description)
        if puzzle_match:
            universe.puzzle_link = puzzle_match.group(1)
        
        # Parse Plakate
        poster_matches = re.findall(r'- (bilder/.+)', description)
        universe.posters = poster_matches
        
        return universe
