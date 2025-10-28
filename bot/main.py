"""
Halloween Bot - Haupteinstiegspunkt
Rebellion gegen die KI - Halloween Party 2025
"""

import asyncio
import sys
import logging
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)

# Lokale Imports
from config import config
from services.logger import BotLogger, log_user_action, log_error
from database.db import db
from database.crud import create_team, get_team_by_id
from utils.yaml_loader import universe_loader


def init_database():
    """Initialisiert Datenbank und lädt Teams."""
    logger = logging.getLogger('bot.main')
    
    # Datenbank-Tabellen erstellen
    db.create_tables()
    logger.info("Database tables initialized")
    
    # Teams aus YAML laden
    teams_data = universe_loader.get_teams()
    
    with db.get_session() as session:
        loaded_count = 0
        for team_data in teams_data:
            # Prüfen ob Team bereits existiert
            existing = get_team_by_id(session, team_data['team_id'])
            
            if not existing:
                create_team(
                    session=session,
                    team_id=team_data['team_id'],
                    film_title=team_data['film_title'],
                    character_1=team_data['character_1'],
                    character_2=team_data['character_2'],
                    character_1_id=team_data['character_1_id'],
                    character_2_id=team_data['character_2_id'],
                    puzzle_link=team_data['puzzle_link']
                )
                loaded_count += 1
        
        if loaded_count > 0:
            logger.info(f"Loaded {loaded_count} new teams from YAML")


def main():
    """Hauptfunktion - Startet den Bot."""
    
    # Logging initialisieren
    bot_logger = BotLogger(
        logs_base_path=str(config.LOGS_BASE_PATH),
        log_level=config.LOG_LEVEL
    )
    logger = bot_logger.get_logger('bot.main')
    
    logger.info("=" * 60)
    logger.info("Halloween Bot startet...")
    logger.info(f"Konfiguration: {config}")
    logger.info("=" * 60)
    
    # Datenbank initialisieren
    init_database()
    
    try:
        # Bot-Application erstellen
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Command-Handler registrieren
        from handlers.start import start_command
        from handlers.help import help_command
        from handlers.points import points_command
        from handlers.photo import photo_handler
        from handlers.text import text_handler
        from handlers.team import team_command
        from handlers.keyboard import keyboard_handler
        from handlers.admin import (
            admin_help_command,
            admin_command,
            admin_players_command,
            admin_player_command,
            admin_teams_command,
            admin_stats_command,
            admin_points_command,
            admin_eastereggs_command,
            admin_reset_command,
            admin_apiusage_command,
            admin_broadcast_command,
            admin_message_command,
            admin_team_message_command
        )
        
        # User Commands
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        application.add_handler(CommandHandler("punkte", points_command))
        application.add_handler(CommandHandler("team", team_command))
        
        # Admin Commands (mit kurzen Aliasen)
        application.add_handler(CommandHandler("admin", admin_command))
        application.add_handler(CommandHandler(["help_admin", "adminhelp"], admin_help_command))
        
        # Admin: Spieler-Verwaltung
        application.add_handler(CommandHandler(["players", "admin_players"], admin_players_command))
        application.add_handler(CommandHandler(["player", "admin_player"], admin_player_command))
        application.add_handler(CommandHandler(["points", "admin_points"], admin_points_command))
        
        # Admin: Teams & Statistiken
        application.add_handler(CommandHandler(["teams", "admin_teams"], admin_teams_command))
        application.add_handler(CommandHandler(["stats", "admin_stats"], admin_stats_command))
        application.add_handler(CommandHandler(["eastereggs", "films", "admin_eastereggs"], admin_eastereggs_command))
        
        # Admin: Nachrichten
        application.add_handler(CommandHandler(["broadcast", "admin_broadcast"], admin_broadcast_command))
        application.add_handler(CommandHandler(["message", "admin_message"], admin_message_command))
        application.add_handler(CommandHandler(["teammessage", "admin_teammessage"], admin_team_message_command))
        
        # Admin: System
        application.add_handler(CommandHandler(["apiusage", "admin_apiusage"], admin_apiusage_command))
        application.add_handler(CommandHandler(["reset", "admin_reset"], admin_reset_command))
        
        # Keyboard-Button Handler (VOR text_handler!)
        application.add_handler(MessageHandler(
            filters.TEXT & ~filters.COMMAND & 
            filters.Regex(r'^(🏆 Meine Punkte|❓ Hilfe|ℹ️ Anleitung)$'),
            keyboard_handler
        ))
        
        # Foto-Handler (ohne Command)
        application.add_handler(MessageHandler(filters.PHOTO, photo_handler))
        
        # Text-Handler für Team-Beitritt (ohne Command - DEPRECATED, nutze /team)
        application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
        
        logger.info("Bot-Handler registriert")
        logger.info(f"Admin-User-IDs: {config.ADMIN_USER_IDS}")
        
        # Bot starten
        logger.info("Bot läuft... (Strg+C zum Beenden)")
        application.run_polling(allowed_updates=Update.ALL_TYPES)
        
    except KeyboardInterrupt:
        logger.info("Bot wird beendet (KeyboardInterrupt)...")
        sys.exit(0)
        
    except Exception as e:
        log_error(logger, e, context="main()")
        sys.exit(1)


if __name__ == '__main__':
    main()
