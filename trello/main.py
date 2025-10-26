"""
CLI-Tool für Halloween25 Trello-Synchronisation
"""
import argparse
import sys
from pathlib import Path
from configparser import ConfigParser
from sync_manager import SyncManager


def load_config(config_path: str = 'config.ini') -> dict:
    """Lädt die Konfiguration"""
    config = ConfigParser()
    
    if not Path(config_path).exists():
        print(f"❌ Konfigurationsdatei nicht gefunden: {config_path}")
        print("Bitte erstelle eine config.ini mit folgenden Werten:")
        print("""
[trello]
api_key = DEIN_API_KEY
api_token = DEIN_API_TOKEN
board_id = DEINE_BOARD_ID

[paths]
markdown = ../notes/Universen.md
yaml = universen.yaml
        """)
        sys.exit(1)
    
    config.read(config_path, encoding='utf-8')
    
    return {
        'api_key': config.get('trello', 'api_key'),
        'api_token': config.get('trello', 'api_token'),
        'board_id': config.get('trello', 'board_id'),
        'markdown_path': config.get('paths', 'markdown'),
        'yaml_path': config.get('paths', 'yaml'),
        'list_name': config.get('paths', 'list_name', fallback='Universen/Easter Eggs')
    }


def main():
    parser = argparse.ArgumentParser(
        description='Halloween25 Trello Synchronisations-Tool',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Beispiele:
  %(prog)s push           # Synchronisiert Markdown → Trello
  %(prog)s pull           # Synchronisiert Trello → Markdown
  %(prog)s sync           # Bidirektionale Synchronisation
  %(prog)s export         # Exportiert Markdown → YAML
  %(prog)s import         # Importiert YAML → Markdown
        """
    )
    
    parser.add_argument(
        'command',
        choices=['push', 'pull', 'sync', 'export', 'import'],
        help='Auszuführender Befehl'
    )
    
    parser.add_argument(
        '-c', '--config',
        default='config.ini',
        help='Pfad zur Konfigurationsdatei (Standard: config.ini)'
    )
    
    args = parser.parse_args()
    
    # Lade Konfiguration
    config = load_config(args.config)
    
    # Erstelle SyncManager
    sync_manager = SyncManager(
        markdown_path=config['markdown_path'],
        yaml_path=config['yaml_path'],
        trello_api_key=config['api_key'],
        trello_api_token=config['api_token'],
        trello_board_id=config['board_id'],
        list_name=config['list_name']
    )
    
    # Führe Befehl aus
    try:
        if args.command == 'push':
            sync_manager.push_to_trello()
        elif args.command == 'pull':
            sync_manager.pull_from_trello()
        elif args.command == 'sync':
            sync_manager.sync()
        elif args.command == 'export':
            sync_manager.export_to_yaml()
        elif args.command == 'import':
            sync_manager.import_from_yaml()
    except Exception as e:
        print(f"\n❌ Fehler: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
