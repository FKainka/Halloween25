"""
Konfigurationsverwaltung für den Halloween Bot.
Lädt alle Einstellungen aus .env und stellt sie bereit.
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv


class Config:
    """Zentrale Konfigurationsklasse."""
    
    def __init__(self):
        """Lädt Konfiguration aus .env Datei."""
        # .env Datei laden
        load_dotenv()
        
        # Bot Configuration
        self.TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
        if not self.TELEGRAM_BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN nicht in .env gefunden!")
        
        # OpenAI API
        self.OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        
        # Database
        self.DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///bot.db')
        
        # Admin User IDs
        admin_ids_str = os.getenv('ADMIN_USER_IDS', '')
        self.ADMIN_USER_IDS: List[int] = []
        if admin_ids_str:
            try:
                self.ADMIN_USER_IDS = [
                    int(uid.strip()) 
                    for uid in admin_ids_str.split(',') 
                    if uid.strip()
                ]
            except ValueError as e:
                raise ValueError(f"Fehler beim Parsen von ADMIN_USER_IDS: {e}")
        
        # Environment
        self.ENVIRONMENT = os.getenv('ENVIRONMENT', 'development')
        self.LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
        
        # File Storage - alle Daten im data/ Verzeichnis
        script_dir = Path(__file__).parent
        data_base_path = os.getenv('DATA_BASE_PATH', './data')
        data_path = script_dir / data_base_path if not Path(data_base_path).is_absolute() else Path(data_base_path)
        
        self.PHOTOS_BASE_PATH = data_path / 'photos'
        self.LOGS_BASE_PATH = data_path / 'logs'
        
        # AI Settings
        self.AI_CONFIDENCE_THRESHOLD = int(
            os.getenv('AI_CONFIDENCE_THRESHOLD', '70')
        )
        self.AI_TIMEOUT_SECONDS = int(
            os.getenv('AI_TIMEOUT_SECONDS', '15')
        )
        
        # Pfade sicherstellen
        self._ensure_paths()
    
    def _ensure_paths(self):
        """Stellt sicher, dass alle benötigten Verzeichnisse existieren."""
        # Foto-Verzeichnisse
        (self.PHOTOS_BASE_PATH / 'party').mkdir(parents=True, exist_ok=True)
        (self.PHOTOS_BASE_PATH / 'films').mkdir(parents=True, exist_ok=True)
        (self.PHOTOS_BASE_PATH / 'puzzles').mkdir(parents=True, exist_ok=True)
        (self.PHOTOS_BASE_PATH / 'thumbnails').mkdir(parents=True, exist_ok=True)
        
        # Log-Verzeichnis
        self.LOGS_BASE_PATH.mkdir(parents=True, exist_ok=True)
    
    def is_admin(self, user_id: int) -> bool:
        """
        Prüft, ob ein User Admin-Rechte hat.
        
        Args:
            user_id: Telegram User-ID
        
        Returns:
            bool: True wenn User Admin ist
        """
        return user_id in self.ADMIN_USER_IDS
    
    def is_production(self) -> bool:
        """Prüft, ob Bot im Production-Modus läuft."""
        return self.ENVIRONMENT.lower() == 'production'
    
    def is_development(self) -> bool:
        """Prüft, ob Bot im Development-Modus läuft."""
        return self.ENVIRONMENT.lower() == 'development'
    
    def __repr__(self) -> str:
        """String-Repräsentation der Config (ohne sensible Daten)."""
        return (
            f"Config(environment={self.ENVIRONMENT}, "
            f"log_level={self.LOG_LEVEL}, "
            f"admin_count={len(self.ADMIN_USER_IDS)}, "
            f"ai_threshold={self.AI_CONFIDENCE_THRESHOLD}%)"
        )


# Globale Config-Instanz
config = Config()
