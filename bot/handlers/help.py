"""
/help Command Handler
Zeigt detaillierte Hilfe und Spielregeln.
"""

from telegram import Update
from telegram.ext import ContextTypes

from services.logger import BotLogger, log_user_action
from services.template_manager import template_manager


logger = BotLogger.get_logger('bot.handlers.help')


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /help Command.
    Sendet detaillierte Hilfe-Informationen.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} ({user.first_name}) executed /help command")
    
    try:
        # Hilfetext aus Template rendern
        help_text = template_manager.render_help(
            first_name=user.first_name or "Reisender"
        )
        
        # Nachricht senden
        await context.bot.send_message(
            chat_id=chat_id,
            text=help_text
        )
        
        logger.debug(f"Help message sent to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in help_command for user {user.id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
