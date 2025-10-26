"""
/start Command Handler
Begrüßt neue User und registriert sie in der Datenbank.
"""

from telegram import Update
from telegram.ext import ContextTypes

from config import config
from services.logger import BotLogger, log_user_action
from services.template_manager import template_manager


logger = BotLogger.get_logger('bot.handlers.start')


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /start Command.
    Registriert User und sendet Begrüßungstext.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} ({user.first_name}) executed /start command")
    
    try:
        # TODO: User in Datenbank registrieren (wenn noch nicht vorhanden)
        # from database.crud import get_or_create_user
        # db_user = get_or_create_user(user.id, user.username, user.first_name, user.last_name)
        
        # Begrüßungstext aus Template rendern
        welcome_text = template_manager.render_welcome(
            first_name=user.first_name or "Reisender"
        )
        
        # Admin-Hinweis für Admins
        admin_note = ""
        if config.is_admin(user.id):
            admin_note = "\n\n🔧 Admin-Modus aktiviert"
            logger.info(f"Admin user {user.id} detected")
        
        # Nachricht senden
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text + admin_note
        )
        
        logger.debug(f"Welcome message sent to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in start_command for user {user.id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
