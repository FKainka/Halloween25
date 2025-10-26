"""
YAML-Loader für universen.yaml - lädt Film/Team-Daten.
"""

import yaml
from pathlib import Path
from typing import List, Dict, Any
import logging

logger = logging.getLogger('bot.utils.yaml_loader')


class UniverseLoader:
    """Lädt und verarbeitet universen.yaml."""
    
    def __init__(self, yaml_path: str = None):
        """
        Initialisiert den Loader.
        
        Args:
            yaml_path: Pfad zur YAML-Datei (default: relativ zu Script)
        """
        if yaml_path is None:
            # Pfad relativ zum bot-Verzeichnis
            script_dir = Path(__file__).parent.parent
            yaml_path = script_dir.parent / "notes" / "universen.yaml"
        
        self.yaml_path = Path(yaml_path)
        self.universes = []
        
        if self.yaml_path.exists():
            self.load()
        else:
            logger.error(f"YAML file not found: {self.yaml_path}")
    
    def load(self) -> List[Dict[str, Any]]:
        """
        Lädt die YAML-Datei.
        
        Returns:
            List[Dict]: Liste von Universe-Dictionaries
        """
        try:
            with open(self.yaml_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                self.universes = data.get('universes', [])
                logger.info(f"Loaded {len(self.universes)} universes from YAML")
                return self.universes
        except Exception as e:
            logger.error(f"Error loading YAML: {e}", exc_info=True)
            return []
    
    def get_teams(self) -> List[Dict[str, Any]]:
        """
        Extrahiert Team-Daten aus Universes.
        
        Returns:
            List[Dict]: Team-Informationen
        """
        teams = []
        
        for universe in self.universes:
            # Nur Universen mit vollständigen Team-Daten
            if not universe.get('team_id') or not universe.get('characters'):
                continue
            
            characters = universe.get('characters', [])
            if len(characters) < 2:
                continue
            
            team = {
                'team_id': universe['team_id'],
                'film_title': universe.get('title', 'Unknown'),
                'character_1': characters[0].get('name', ''),
                'character_2': characters[1].get('name', ''),
                'character_1_id': characters[0].get('id', ''),
                'character_2_id': characters[1].get('id', ''),
                'puzzle_link': universe.get('puzzle_link', ''),
                'easter_egg': universe.get('easter_egg', {}),
                'film_clip': universe.get('film_clip', ''),
                'posters': universe.get('posters', [])
            }
            
            teams.append(team)
        
        logger.info(f"Extracted {len(teams)} teams from universes")
        return teams
    
    def get_films(self) -> List[str]:
        """
        Gibt Liste aller Film-Titel zurück.
        
        Returns:
            List[str]: Film-Titel
        """
        return [u.get('title') for u in self.universes if u.get('title')]


# Globale Instanz
universe_loader = UniverseLoader()
