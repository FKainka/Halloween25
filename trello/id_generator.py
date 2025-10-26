"""
ID-Generator für Charaktere und Teams
"""
import hashlib


class IDGenerator:
    """Generiert 6-stellige IDs für Charaktere und berechnet Team-IDs"""
    
    @staticmethod
    def generate_character_id(name: str, max_value: int = 499999) -> str:
        """
        Generiert eine 6-stellige ID aus einem Charakternamen.
        Die ID ist deterministisch (gleicher Name = gleiche ID) und <= max_value.
        
        Args:
            name: Name des Charakters
            max_value: Maximaler Wert (Standard: 499999, damit Team-ID 6-stellig bleibt)
        
        Returns:
            6-stellige ID als String
        """
        # Erstelle Hash aus dem Namen
        hash_object = hashlib.md5(name.lower().strip().encode('utf-8'))
        hash_hex = hash_object.hexdigest()
        
        # Konvertiere zu Dezimalzahl und begrenze auf max_value
        hash_int = int(hash_hex, 16)
        char_id = (hash_int % max_value) + 1  # +1 damit nie 0
        
        # Formatiere als 6-stellige Zahl mit führenden Nullen
        return f"{char_id:06d}"
    
    @staticmethod
    def calculate_team_id(char_id1: str, char_id2: str) -> str:
        """
        Berechnet die Team-ID als Summe zweier Charakter-IDs.
        
        Args:
            char_id1: Erste Charakter-ID
            char_id2: Zweite Charakter-ID
        
        Returns:
            6-stellige Team-ID als String
        """
        id1 = int(char_id1)
        id2 = int(char_id2)
        team_id = id1 + id2
        
        # Stelle sicher, dass die Team-ID 6-stellig ist
        if team_id > 999999:
            team_id = team_id % 1000000
        
        return f"{team_id:06d}"
    
    @staticmethod
    def generate_ids_for_universe(universe) -> None:
        """
        Generiert automatisch IDs für alle Charaktere in einem Universum
        und berechnet die Team-ID.
        
        Args:
            universe: Universe-Objekt mit Charakteren
        """
        if not universe.characters:
            return
        
        # Generiere IDs für alle Charaktere ohne ID
        for char in universe.characters:
            if not char.character_id:
                char.character_id = IDGenerator.generate_character_id(char.name)
        
        # Aktualisiere character_ids Liste
        universe.character_ids = [char.character_id for char in universe.characters]
        
        # Berechne Team-ID, falls mindestens 2 Charaktere vorhanden
        if len(universe.characters) >= 2:
            universe.team_id = IDGenerator.calculate_team_id(
                universe.characters[0].character_id,
                universe.characters[1].character_id
            )
