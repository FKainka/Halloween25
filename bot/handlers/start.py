"""
/start Command Handler
Begrüßt neue User und registriert sie in der Datenbank.
"""

from pathlib import Path
from telegram import Update, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import ContextTypes

from config import config
from services.logger import BotLogger, log_user_action
from services.template_manager import template_manager
from database.db import db
from database.crud import get_or_create_user


logger = BotLogger.get_logger('bot.handlers.start')


def get_main_keyboard() -> ReplyKeyboardMarkup:
    """
    Erstellt das Haupt-Keyboard mit den wichtigsten Aktionen.
    
    Returns:
        ReplyKeyboardMarkup: Keyboard mit Buttons
    """
    keyboard = [
        [KeyboardButton("🏆 Meine Punkte"), KeyboardButton("❓ Hilfe")],
        [KeyboardButton("ℹ️ Anleitung")]
    ]
    
    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        one_time_keyboard=False
    )


async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /start Command.
    Registriert User und sendet Begrüßungstext mit Custom Keyboard.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} ({user.first_name}) executed /start command")
    
    try:
        # User in Datenbank registrieren
        with db.get_session() as session:
            db_user = get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
        
        # Begrüßungstext aus Template rendern
        welcome_text = template_manager.render_welcome(
            first_name=user.first_name or "Reisender"
        )
        
        # Admin-Hinweis für Admins
        admin_note = ""
        if config.is_admin(user.id):
            admin_note = "\n\n🔧 Admin-Modus aktiviert"
            logger.info(f"Admin user {user.id} detected")
        
        # Titelbild senden
        titel_image_path = Path(__file__).parent.parent / 'templates' / 'titel.jpg'
        
        if titel_image_path.exists():
            try:
                with open(titel_image_path, 'rb') as photo:
                    await context.bot.send_photo(
                        chat_id=chat_id,
                        photo=photo,
                        caption="🎃 Halloween Party 2025 - Rebellion gegen die KI 🤖"
                    )
            except Exception as e:
                logger.warning(f"Could not send title image: {e}")
        
        # Nachricht mit Custom Keyboard senden
        await context.bot.send_message(
            chat_id=chat_id,
            text=welcome_text + admin_note,
            reply_markup=get_main_keyboard()
        )
        
        logger.debug(f"Welcome message sent to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in start_command for user {user.id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
