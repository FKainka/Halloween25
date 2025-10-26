"""
YAML-Konverter für Universen
"""
import yaml
from typing import List
from pathlib import Path
from models import Universe
from markdown_parser import MarkdownParser


class YAMLConverter:
    """Konvertiert zwischen Markdown und YAML"""
    
    def __init__(self, markdown_path: str, yaml_path: str):
        self.markdown_path = markdown_path
        self.yaml_path = yaml_path
        self.parser = MarkdownParser(markdown_path)
    
    def markdown_to_yaml(self) -> None:
        """Konvertiert Universen.md zu YAML"""
        universes = self.parser.parse()
        
        # Konvertiere zu Dict-Liste
        data = {
            'universes': [u.to_dict() for u in universes]
        }
        
        # Schreibe YAML
        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
        
        print(f"✓ {len(universes)} Universen wurden nach YAML exportiert: {self.yaml_path}")
    
    def yaml_to_markdown(self) -> None:
        """Konvertiert YAML zurück zu Markdown"""
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        # Konvertiere zu Universe-Objekten
        universes = [Universe.from_dict(u) for u in data['universes']]
        
        # Generiere Markdown
        markdown_content = self.parser.universes_to_markdown(universes)
        
        # Schreibe Markdown
        with open(self.markdown_path, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        print(f"✓ {len(universes)} Universen wurden nach Markdown exportiert: {self.markdown_path}")
    
    def load_from_yaml(self) -> List[Universe]:
        """Lädt Universen aus YAML-Datei"""
        with open(self.yaml_path, 'r', encoding='utf-8') as f:
            data = yaml.safe_load(f)
        
        return [Universe.from_dict(u) for u in data['universes']]
    
    def save_to_yaml(self, universes: List[Universe]) -> None:
        """Speichert Universen in YAML-Datei"""
        data = {
            'universes': [u.to_dict() for u in universes]
        }
        
        with open(self.yaml_path, 'w', encoding='utf-8') as f:
            yaml.dump(data, f, allow_unicode=True, sort_keys=False, default_flow_style=False)
