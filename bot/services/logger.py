"""
Logging-Konfiguration für den Halloween Bot.
Erstellt strukturierte Logs mit verschiedenen Log-Levels und separaten Dateien.
"""

import logging
import os
from logging.handlers import RotatingFileHandler
from pathlib import Path
from datetime import datetime


# ANSI Color Codes für farbiges Logging
class LogColors:
    """ANSI Farb-Codes für Terminal-Output."""
    RESET = '\033[0m'
    BOLD = '\033[1m'
    
    # Log-Level Farben
    DEBUG = '\033[36m'      # Cyan
    INFO = '\033[32m'       # Grün
    WARNING = '\033[33m'    # Gelb
    ERROR = '\033[31m'      # Rot
    CRITICAL = '\033[35m'   # Magenta
    
    # Spezielle Farben
    USER = '\033[34m'       # Blau
    TEMPLATE = '\033[36m'   # Cyan


class ColoredFormatter(logging.Formatter):
    """Formatter mit Farbunterstützung für Console-Output."""
    
    COLORS = {
        'DEBUG': LogColors.DEBUG,
        'INFO': LogColors.INFO,
        'WARNING': LogColors.WARNING,
        'ERROR': LogColors.ERROR,
        'CRITICAL': LogColors.CRITICAL,
    }
    
    def format(self, record):
        # Farbe basierend auf Log-Level
        color = self.COLORS.get(record.levelname, LogColors.RESET)
        
        # Formatiere die Nachricht
        log_message = super().format(record)
        
        # Füge Farbe hinzu
        return f"{color}{log_message}{LogColors.RESET}"


class BotLogger:
    """Zentrale Logging-Konfiguration für den Bot."""
    
    def __init__(self, logs_base_path: str = "./logs", log_level: str = "INFO"):
        """
        Initialisiert das Logging-System.
        
        Args:
            logs_base_path: Basis-Pfad für Log-Dateien
            log_level: Log-Level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        self.logs_path = Path(logs_base_path)
        self.logs_path.mkdir(parents=True, exist_ok=True)
        
        # Log-Level aus String konvertieren
        self.log_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # Log-Format definieren
        self.log_format = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Farbiges Format für Console
        self.colored_format = ColoredFormatter(
            '[%(asctime)s] %(levelname)-8s [%(name)s] %(message)s',
            datefmt='%H:%M:%S'
        )
        
        # Logger konfigurieren
        self._setup_loggers()
    
    def _setup_loggers(self):
        """Richtet alle Logger mit ihren Handlern ein."""
        # Root Logger
        root_logger = logging.getLogger()
        root_logger.setLevel(self.log_level)
        
        # HTTP-Request-Logger deaktivieren (zu verbose)
        logging.getLogger("httpx").setLevel(logging.WARNING)
        logging.getLogger("httpcore").setLevel(logging.WARNING)
        logging.getLogger("telegram").setLevel(logging.WARNING)
        
        # Console Handler (für wichtige Events) mit Farben
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(self.colored_format)
        root_logger.addHandler(console_handler)
        
        # Bot-Log (alle Events)
        bot_handler = self._create_rotating_handler(
            filename="bot.log",
            level=self.log_level
        )
        root_logger.addHandler(bot_handler)
        
        # Error-Log (nur Fehler)
        error_handler = self._create_rotating_handler(
            filename="errors.log",
            level=logging.ERROR
        )
        root_logger.addHandler(error_handler)
        
        # AI-Evaluations-Log (speziell für KI-Bewertungen)
        ai_logger = logging.getLogger('bot.services.ai')
        ai_handler = self._create_rotating_handler(
            filename="ai_evaluations.log",
            level=logging.DEBUG
        )
        ai_logger.addHandler(ai_handler)
    
    def _create_rotating_handler(
        self, 
        filename: str, 
        level: int,
        max_bytes: int = 10 * 1024 * 1024,  # 10 MB
        backup_count: int = 7  # 7 Tage
    ) -> RotatingFileHandler:
        """
        Erstellt einen Rotating File Handler.
        
        Args:
            filename: Name der Log-Datei
            level: Log-Level für diesen Handler
            max_bytes: Maximale Größe pro Log-Datei
            backup_count: Anzahl der Backup-Dateien
        
        Returns:
            RotatingFileHandler: Konfigurierter Handler
        """
        file_path = self.logs_path / filename
        handler = RotatingFileHandler(
            filename=str(file_path),
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        handler.setLevel(level)
        handler.setFormatter(self.log_format)
        return handler
    
    @staticmethod
    def get_logger(name: str) -> logging.Logger:
        """
        Gibt einen Logger mit dem angegebenen Namen zurück.
        
        Args:
            name: Name des Loggers (z.B. 'bot.handlers.start')
        
        Returns:
            logging.Logger: Konfigurierter Logger
        """
        return logging.getLogger(name)


def log_user_action(logger: logging.Logger, user_id: int, action: str, details: str = ""):
    """
    Hilfsfunktion zum Loggen von User-Aktionen.
    
    Args:
        logger: Logger-Instanz
        user_id: Telegram User-ID
        action: Beschreibung der Aktion
        details: Zusätzliche Details
    """
    message = f"User {user_id}: {action}"
    if details:
        message += f" | {details}"
    logger.info(message)


def log_ai_evaluation(
    logger: logging.Logger, 
    user_id: int, 
    film_title: str, 
    confidence: float,
    is_approved: bool,
    reasoning: str
):
    """
    Hilfsfunktion zum Loggen von KI-Bewertungen.
    
    Args:
        logger: Logger-Instanz
        user_id: Telegram User-ID
        film_title: Name des Films
        confidence: Confidence-Score (0-100)
        is_approved: Ob das Foto akzeptiert wurde
        reasoning: Begründung der KI
    """
    status = "APPROVED" if is_approved else "REJECTED"
    logger.info(
        f"AI Evaluation | User {user_id} | Film: {film_title} | "
        f"Status: {status} | Confidence: {confidence}% | Reasoning: {reasoning}"
    )


def log_error(logger: logging.Logger, error: Exception, context: str = ""):
    """
    Hilfsfunktion zum Loggen von Fehlern mit Context.
    
    Args:
        logger: Logger-Instanz
        error: Exception-Objekt
        context: Kontext, in dem der Fehler auftrat
    """
    message = f"ERROR in {context}: {type(error).__name__}: {str(error)}"
    logger.error(message, exc_info=True)
