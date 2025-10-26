"""
Halloween Bot - Haupteinstiegspunkt
Rebellion gegen die KI - Halloween Party 2025
"""

import asyncio
import sys
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
    
    try:
        # Bot-Application erstellen
        application = Application.builder().token(config.TELEGRAM_BOT_TOKEN).build()
        
        # Command-Handler registrieren
        from handlers import start_command, help_command
        application.add_handler(CommandHandler("start", start_command))
        application.add_handler(CommandHandler("help", help_command))
        
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
