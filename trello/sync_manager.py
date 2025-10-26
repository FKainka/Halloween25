"""
Synchronisations-Manager für Universen zwischen Markdown, YAML und Trello
"""
from typing import List, Dict, Optional
from models import Universe
from markdown_parser import MarkdownParser
from yaml_converter import YAMLConverter
from trello_client import TrelloClient
from id_generator import IDGenerator
from pathlib import Path


class SyncManager:
    """Verwaltet die Synchronisation zwischen verschiedenen Datenquellen"""
    
    def __init__(
        self,
        markdown_path: str,
        yaml_path: str,
        trello_api_key: str,
        trello_api_token: str,
        trello_board_id: str,
        list_name: str = 'Universen/Easter Eggs'
    ):
        self.markdown_path = markdown_path
        self.yaml_path = yaml_path
        self.parser = MarkdownParser(markdown_path)
        self.yaml_converter = YAMLConverter(markdown_path, yaml_path)
        self.trello = TrelloClient(trello_api_key, trello_api_token, trello_board_id)
        self.universen_list_name = list_name
    
    def push_to_trello(self) -> None:
        """Synchronisiert Markdown → Trello"""
        print("📤 Push zu Trello...")
        
        # Lade Universen aus Markdown
        universes = self.parser.parse()
        
        # Stelle sicher, dass die Ziel-Liste existiert
        list_id = self.trello.get_or_create_list(self.universen_list_name)
        
        # Hole bestehende Karten
        existing_cards = self.trello.get_all_cards()
        cards_by_title = {card['name']: card for card in existing_cards}
        
        created = 0
        updated = 0
        
        for universe in universes:
            # Schreibe alle Karten in die gleiche Liste
            if universe.title in cards_by_title:
                # Update bestehende Karte
                card = cards_by_title[universe.title]
                self.trello.update_card(card['id'], universe)
                universe.trello_card_id = card['id']
                universe.trello_list_id = list_id
                updated += 1
                print(f"  ✓ Aktualisiert: {universe.title}")
            else:
                # Erstelle neue Karte
                card_id = self.trello.create_card(list_id, universe)
                universe.trello_card_id = card_id
                universe.trello_list_id = list_id
                created += 1
                print(f"  ✓ Erstellt: {universe.title}")
        
        # Speichere aktualisierte Daten zurück
        self.yaml_converter.save_to_yaml(universes)
        
        print(f"\n✅ Push abgeschlossen: {created} erstellt, {updated} aktualisiert")
    
    def pull_from_trello(self) -> None:
        """Synchronisiert Trello → Markdown"""
        print("📥 Pull von Trello...")
        
        # Lade alle Karten von Trello
        all_cards = self.trello.get_all_cards()
        
        # Lade bestehende Universen (für Metadaten)
        try:
            existing_universes = self.yaml_converter.load_from_yaml()
            universes_by_id = {u.trello_card_id: u for u in existing_universes if u.trello_card_id}
        except:
            universes_by_id = {}
        
        # Konvertiere Karten zu Universen
        universes = []
        for card in all_cards:
            # Nur Karten aus der Ziel-Liste berücksichtigen
            if card['idList'] != self.trello.get_or_create_list(self.universen_list_name):
                continue
            universe = self.trello.parse_card_to_universe(card)
            universe.status = 'fertiggeplant'  # Standardstatus, da alle in einer Liste
            # Übernehme zusätzliche Daten aus bestehendem Universum
            if card['id'] in universes_by_id:
                existing = universes_by_id[card['id']]
                if not universe.posters and existing.posters:
                    universe.posters = existing.posters
            universes.append(universe)
            print(f"  ✓ Geladen: {universe.title}")
        
        # Speichere zu YAML und Markdown
        self.yaml_converter.save_to_yaml(universes)
        markdown_content = self.parser.universes_to_markdown(universes)
        
        with open(self.markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"\n✅ Pull abgeschlossen: {len(universes)} Universen synchronisiert")
    
    def sync(self) -> None:
        """Bidirektionale Synchronisation (Trello hat Vorrang)"""
        print("🔄 Bidirektionale Synchronisation...\n")
        
        # Zuerst Pull (Trello-Daten haben Vorrang)
        self.pull_from_trello()
        
        print("\n" + "="*50 + "\n")
        
        # Dann Push (falls lokale Änderungen)
        self.push_to_trello()
    
    def export_to_yaml(self) -> None:
        """Exportiert Markdown zu YAML"""
        self.yaml_converter.markdown_to_yaml()
    
    def import_from_yaml(self) -> None:
        """Importiert YAML zu Markdown"""
        self.yaml_converter.yaml_to_markdown()
    
    def generate_character_ids(self) -> None:
        """Generiert automatisch IDs für alle Charaktere und speichert zurück"""
        print("🔢 Generiere Charakter-IDs...\n")
        
        # Lade Universen aus Markdown
        universes = self.parser.parse()
        
        updated_count = 0
        
        for universe in universes:
            if not universe.characters:
                continue
            
            # Prüfe ob IDs fehlen
            needs_update = False
            for char in universe.characters:
                if not char.character_id:
                    needs_update = True
                    break
            
            if not universe.team_id and len(universe.characters) >= 2:
                needs_update = True
            
            if needs_update:
                # Generiere IDs
                IDGenerator.generate_ids_for_universe(universe)
                updated_count += 1
                
                # Zeige generierte IDs
                print(f"✓ {universe.title}:")
                for char in universe.characters:
                    print(f"  - {char.name}: {char.character_id}")
                if universe.team_id:
                    print(f"  → Team-ID: {universe.team_id}")
                print()
        
        if updated_count > 0:
            # Speichere zurück zu YAML und Markdown
            self.yaml_converter.save_to_yaml(universes)
            markdown_content = self.parser.universes_to_markdown(universes)
            
            with open(self.markdown_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)
            
            print(f"✅ {updated_count} Universen wurden mit IDs aktualisiert")
        else:
            print("ℹ️  Alle Universen haben bereits IDs")
