"""
Foto-Manager - Speichert Fotos lokal und erstellt Thumbnails.
"""

import os
from pathlib import Path
from PIL import Image
from datetime import datetime
import logging

from config import config

logger = logging.getLogger('bot.services.photo')


class PhotoManager:
    """Verwaltet lokale Foto-Speicherung und Thumbnails."""
    
    def __init__(self):
        """Initialisiert Photo-Manager."""
        self.photos_base = config.PHOTOS_BASE_PATH
        self.thumbnail_size = (200, 200)
        
        # Verzeichnisse sicherstellen
        self._ensure_directories()
    
    def _ensure_directories(self):
        """Stellt sicher, dass alle Verzeichnisse existieren."""
        (self.photos_base / 'party').mkdir(parents=True, exist_ok=True)
        (self.photos_base / 'films').mkdir(parents=True, exist_ok=True)
        (self.photos_base / 'puzzles').mkdir(parents=True, exist_ok=True)
        (self.photos_base / 'thumbnails').mkdir(parents=True, exist_ok=True)
    
    def save_photo(
        self,
        photo_bytes: bytes,
        user_id: int,
        submission_id: int,
        category: str = 'party',
        film_title: str = None,
        user_name: str = None
    ) -> tuple[str, str]:
        """
        Speichert Foto lokal und erstellt Thumbnail.
        
        Args:
            photo_bytes: Foto-Daten
            user_id: Telegram User-ID
            submission_id: Submission-ID
            category: 'party', 'films' oder 'puzzles'
            film_title: Film-Titel (für films-Kategorie)
            user_name: Name des Users (für Dateinamen)
        
        Returns:
            tuple: (photo_path, thumbnail_path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Dateiname mit User-Name am Anfang wenn vorhanden
        if user_name:
            sanitized_name = self._sanitize_filename(user_name)
            filename = f"{sanitized_name}_{user_id}_{timestamp}_{submission_id}.jpg"
        else:
            filename = f"{user_id}_{timestamp}_{submission_id}.jpg"
        
        # Ziel-Verzeichnis
        if category == 'films' and film_title:
            # Film-spezifischer Ordner
            film_folder = self._sanitize_filename(film_title)
            target_dir = self.photos_base / 'films' / film_folder
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.photos_base / category
        
        photo_path = target_dir / filename
        thumbnail_path = self.photos_base / 'thumbnails' / filename
        
        try:
            # Foto speichern
            with open(photo_path, 'wb') as f:
                f.write(photo_bytes)
            
            logger.info(f"Photo saved: {photo_path}")
            
            # Thumbnail erstellen
            self._create_thumbnail(photo_path, thumbnail_path)
            
            return (str(photo_path), str(thumbnail_path))
            
        except Exception as e:
            logger.error(f"Error saving photo: {e}", exc_info=True)
            return (None, None)
    
    def _create_thumbnail(self, photo_path: Path, thumbnail_path: Path):
        """
        Erstellt Thumbnail eines Fotos.
        
        Args:
            photo_path: Pfad zum Original-Foto
            thumbnail_path: Pfad zum Thumbnail
        """
        try:
            with Image.open(photo_path) as img:
                # RGB konvertieren (falls RGBA oder andere Modi)
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Thumbnail erstellen (behält Aspect Ratio)
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Speichern
                img.save(thumbnail_path, 'JPEG', quality=85)
                
                logger.debug(f"Thumbnail created: {thumbnail_path}")
                
        except Exception as e:
            logger.error(f"Error creating thumbnail: {e}", exc_info=True)
    
    def _sanitize_filename(self, filename: str) -> str:
        """
        Bereinigt Dateinamen für Dateisystem.
        
        Args:
            filename: Original-Name
        
        Returns:
            str: Bereinigter Name
        """
        # Ersetze ungültige Zeichen
        invalid_chars = '<>:"/\\|?*'
        for char in invalid_chars:
            filename = filename.replace(char, '_')
        
        # Entferne Leerzeichen
        filename = filename.replace(' ', '_')
        
        return filename


# Globale Instanz
photo_manager = PhotoManager()
