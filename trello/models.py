"""
Datenmodelle für die Halloween25 Universen
"""
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Character:
    """Ein Charakter in einem Universum"""
    name: str
    character_id: Optional[str] = None


@dataclass
class EasterEgg:
    """Easter Egg Information"""
    name: str
    description: str
    example_image: Optional[str] = None


@dataclass
class Universe:
    """Ein Film-Universum mit allen Details"""
    title: str
    status: str  # "fertiggeplant", "in_planung", "potentiell"
    
    # Charaktere
    characters: List[Character] = field(default_factory=list)
    character_ids: List[str] = field(default_factory=list)
    team_id: Optional[str] = None
    
    # Easter Egg
    easter_egg: Optional[EasterEgg] = None
    
    # Medien-Links
    film_clip: Optional[str] = None
    puzzle_link: Optional[str] = None
    posters: List[str] = field(default_factory=list)
    
    # Trello-Metadaten
    trello_card_id: Optional[str] = None
    trello_list_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """Konvertiert das Universum in ein Dictionary"""
        return {
            'title': self.title,
            'status': self.status,
            'characters': [
                {
                    'name': char.name,
                    'id': char.character_id
                } for char in self.characters
            ],
            'character_ids': self.character_ids,
            'team_id': self.team_id,
            'easter_egg': {
                'name': self.easter_egg.name,
                'description': self.easter_egg.description,
                'example_image': self.easter_egg.example_image
            } if self.easter_egg else None,
            'film_clip': self.film_clip,
            'puzzle_link': self.puzzle_link,
            'posters': self.posters,
            'trello_card_id': self.trello_card_id,
            'trello_list_id': self.trello_list_id
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Universe':
        """Erstellt ein Universum aus einem Dictionary"""
        characters = [
            Character(
                name=char['name'],
                character_id=char.get('id')
            ) for char in data.get('characters', [])
        ]
        
        easter_egg_data = data.get('easter_egg')
        easter_egg = None
        if easter_egg_data:
            easter_egg = EasterEgg(
                name=easter_egg_data['name'],
                description=easter_egg_data['description'],
                example_image=easter_egg_data.get('example_image')
            )
        
        return cls(
            title=data['title'],
            status=data['status'],
            characters=characters,
            character_ids=data.get('character_ids', []),
            team_id=data.get('team_id'),
            easter_egg=easter_egg,
            film_clip=data.get('film_clip'),
            puzzle_link=data.get('puzzle_link'),
            posters=data.get('posters', []),
            trello_card_id=data.get('trello_card_id'),
            trello_list_id=data.get('trello_list_id')
        )
