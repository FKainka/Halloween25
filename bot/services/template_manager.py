"""
Template-Manager für Bot-Nachrichten.
Verwendet Jinja2 für dynamische Texte.
"""

from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from typing import Dict, Any
import logging

logger = logging.getLogger('bot.services.template')


class TemplateManager:
    """Verwaltet alle Bot-Nachrichten-Templates."""
    
    def __init__(self, templates_path: str = "./templates"):
        """
        Initialisiert den Template-Manager.
        
        Args:
            templates_path: Pfad zum Templates-Verzeichnis
        """
        # Wenn relativer Pfad, dann relativ zum Script-Verzeichnis
        if not Path(templates_path).is_absolute():
            # Pfad relativ zu dieser Datei (services/template_manager.py)
            script_dir = Path(__file__).parent.parent
            self.templates_path = script_dir / templates_path
        else:
            self.templates_path = Path(templates_path)
        
        self.templates_path.mkdir(parents=True, exist_ok=True)
        
        # Jinja2 Environment erstellen
        self.env = Environment(
            loader=FileSystemLoader(str(self.templates_path)),
            trim_blocks=True,
            lstrip_blocks=True
        )
    
    def render(self, template_name: str, **context: Any) -> str:
        """
        Rendert ein Template mit den gegebenen Variablen.
        
        Args:
            template_name: Name der Template-Datei (z.B. 'welcome.txt')
            **context: Variablen für das Template
        
        Returns:
            str: Gerenderter Text
        """
        try:
            template = self.env.get_template(template_name)
            logger.debug(f"Template '{template_name}' erfolgreich geladen")
            return template.render(**context)
        except Exception as e:
            error_msg = f"❌ Fehler beim Laden des Templates '{template_name}': {e}"
            logger.error(f"Template-Fehler: {template_name} nicht gefunden in {self.templates_path}")
            logger.error(f"Exception: {e}", exc_info=True)
            return error_msg
    
    def render_welcome(self, first_name: str) -> str:
        """Rendert Begrüßungstext."""
        return self.render('welcome.txt', first_name=first_name)
    
    def render_help(self, first_name: str) -> str:
        """Rendert Hilfetext."""
        return self.render('help.txt', first_name=first_name)
    
    def render_points(
        self,
        first_name: str,
        total_points: int,
        party_photos_count: int,
        party_points: int,
        film_count: int,
        film_points: int,
        team_points: int,
        puzzle_points: int,
        team_name: str = None,
        recognized_films: list = None,
        ranking: int = None,
        total_users: int = None
    ) -> str:
        """Rendert Punkte-Übersicht."""
        return self.render(
            'points.txt',
            first_name=first_name,
            total_points=total_points,
            party_photos_count=party_photos_count,
            party_points=party_points,
            film_count=film_count,
            film_points=film_points,
            team_points=team_points,
            puzzle_points=puzzle_points,
            team_name=team_name,
            recognized_films=recognized_films or [],
            ranking=ranking,
            total_users=total_users
        )
    
    def render_team_joined(
        self,
        first_name: str,
        team_name: str,
        points: int,
        puzzle_link: str
    ) -> str:
        """Rendert Team-Beitritt-Bestätigung."""
        text = f"""🎉 Willkommen im Team, {first_name}!

Du bist jetzt Teil von Team "{team_name}"!

+{points} Punkte für die Rebellion!

🧩 Hier ist euer Puzzle-Link:
{puzzle_link}

Löse das Puzzle gemeinsam mit deinem Partner und sende dann einen Screenshot des gelösten Puzzles mit der Caption:

Puzzle

Viel Erfolg! 💪"""
        return text
    
    def render_film_approved(
        self,
        first_name: str,
        film_title: str,
        points: int,
        total_points: int,
        ai_reasoning: str = ""
    ) -> str:
        """Rendert Film-Akzeptierung."""
        text = f"""🎬 Hervorragend, {first_name}!

Deine Referenz zu "{film_title}" wurde erkannt!

"""
        if ai_reasoning:
            text += f"{ai_reasoning}\n\n"
        
        text += f"""✅ +{points} Punkte für die Rebellion!

Aktuelle Punkte: {total_points}"""
        return text
    
    def render_film_rejected(
        self,
        first_name: str,
        film_title: str,
        reason: str = ""
    ) -> str:
        """Rendert Film-Ablehnung."""
        text = f"""❌ Leider nicht erkannt, {first_name}

Die Referenz zu "{film_title}" konnte nicht eindeutig erkannt werden.

"""
        if reason:
            text += f"Grund: {reason}\n\n"
        
        text += """Versuche es mit einem deutlicheren Foto oder einem anderen Film!

💡 Tipp: Stelle die Szene nach oder fotografiere das Easter Egg deutlicher."""
        return text
    
    def render_party_photo_thanks(
        self,
        first_name: str,
        points: int = 1,
        total_points: int = 0
    ) -> str:
        """Rendert Dank für Partyfoto."""
        return f"""🎉 Danke für das Partyfoto, {first_name}!

+{points} Punkt für die Rebellion!

Aktuelle Punkte: {total_points}

Weiter so! 📸"""
    
    def render_puzzle_completed(
        self,
        first_name: str,
        points: int,
        total_points: int
    ) -> str:
        """Rendert Puzzle-Abschluss."""
        return f"""🧩 Puzzle gelöst, {first_name}!

Ausgezeichnete Arbeit!

✅ +{points} Punkte für die Rebellion!

Aktuelle Punkte: {total_points}

Die Rebellion ist stolz auf dich! 💪"""
    
    def render_error(self, error_type: str, details: str = "") -> str:
        """Rendert Fehlermeldung."""
        messages = {
            'team_already_joined': "❌ Du bist bereits einem Team beigetreten!",
            'team_invalid': f"❌ Ungültige Team-ID! {details}",
            'film_already_submitted': f"❌ Du hast diesen Film bereits eingereicht! {details}",
            'photo_required': "❌ Bitte sende ein Foto!",
            'caption_required': "❌ Bitte füge eine Beschriftung hinzu!",
            'ai_error': f"⚠️ KI-Bewertung fehlgeschlagen. Wird manuell geprüft. {details}",
            'unknown': f"❌ Ein Fehler ist aufgetreten. {details}"
        }
        return messages.get(error_type, messages['unknown'])


# Globale Template-Manager-Instanz
template_manager = TemplateManager()
