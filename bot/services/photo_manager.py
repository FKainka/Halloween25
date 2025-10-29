"""
Foto-Manager - Speichert Fotos und Videos lokal und erstellt Thumbnails.
"""

import os
from pathlib import Path
from PIL import Image
from datetime import datetime
import logging
import subprocess

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
    
    def save_video(
        self,
        video_bytes: bytes,
        user_id: int,
        submission_id: int,
        category: str = 'party',
        film_title: str = None,
        user_name: str = None
    ) -> tuple[str, str]:
        """
        Speichert Video lokal und erstellt Thumbnail vom ersten Frame.
        
        Args:
            video_bytes: Video-Daten
            user_id: Telegram User-ID
            submission_id: Submission-ID
            category: 'party', 'films' oder 'puzzles'
            film_title: Film-Titel (für films-Kategorie)
            user_name: Name des Users (für Dateinamen)
        
        Returns:
            tuple: (video_path, thumbnail_path)
        """
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # Dateiname mit User-Name am Anfang wenn vorhanden
        if user_name:
            sanitized_name = self._sanitize_filename(user_name)
            filename = f"{sanitized_name}_{user_id}_{timestamp}_{submission_id}.mp4"
        else:
            filename = f"{user_id}_{timestamp}_{submission_id}.mp4"
        
        # Ziel-Verzeichnis
        if category == 'films' and film_title:
            # Film-spezifischer Ordner
            film_folder = self._sanitize_filename(film_title)
            target_dir = self.photos_base / 'films' / film_folder
            target_dir.mkdir(parents=True, exist_ok=True)
        else:
            target_dir = self.photos_base / category
        
        video_path = target_dir / filename
        thumbnail_filename = filename.replace('.mp4', '.jpg')
        thumbnail_path = self.photos_base / 'thumbnails' / thumbnail_filename
        
        try:
            # Video speichern
            with open(video_path, 'wb') as f:
                f.write(video_bytes)
            
            logger.info(f"Video saved: {video_path}")
            
            # Thumbnail vom ersten Frame erstellen (mit ffmpeg)
            self._create_video_thumbnail(video_path, thumbnail_path)
            
            return (str(video_path), str(thumbnail_path))
            
        except Exception as e:
            logger.error(f"Error saving video: {e}", exc_info=True)
            return (None, None)
    
    def _create_video_thumbnail(self, video_path: Path, thumbnail_path: Path):
        """
        Erstellt Thumbnail vom ersten Frame eines Videos mit ffmpeg.
        
        Args:
            video_path: Pfad zum Video
            thumbnail_path: Pfad zum Thumbnail
        """
        try:
            # ffmpeg verwenden um erstes Frame zu extrahieren
            cmd = [
                'ffmpeg',
                '-i', str(video_path),
                '-ss', '00:00:01',  # 1 Sekunde ins Video
                '-vframes', '1',     # Nur 1 Frame
                '-vf', f'scale={self.thumbnail_size[0]}:{self.thumbnail_size[1]}:force_original_aspect_ratio=decrease',
                '-y',  # Überschreibe existierende Datei
                str(thumbnail_path)
            ]
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                logger.debug(f"Video thumbnail created: {thumbnail_path}")
            else:
                logger.warning(f"ffmpeg failed, creating placeholder thumbnail: {result.stderr}")
                # Fallback: Einfaches schwarzes Bild als Placeholder
                self._create_placeholder_thumbnail(thumbnail_path)
                
        except FileNotFoundError:
            logger.warning("ffmpeg not found, creating placeholder thumbnail")
            self._create_placeholder_thumbnail(thumbnail_path)
        except Exception as e:
            logger.error(f"Error creating video thumbnail: {e}", exc_info=True)
            self._create_placeholder_thumbnail(thumbnail_path)
    
    def _create_placeholder_thumbnail(self, thumbnail_path: Path):
        """
        Erstellt ein Placeholder-Thumbnail (schwarzes Bild mit Text).
        
        Args:
            thumbnail_path: Pfad zum Thumbnail
        """
        try:
            # Schwarzes Bild erstellen
            img = Image.new('RGB', self.thumbnail_size, color='black')
            img.save(thumbnail_path, 'JPEG', quality=85)
            logger.debug(f"Placeholder thumbnail created: {thumbnail_path}")
        except Exception as e:
            logger.error(f"Error creating placeholder thumbnail: {e}", exc_info=True)


# Globale Instanz
photo_manager = PhotoManager()
