"""
/anleitung Command Handler
Zeigt Schnellanleitung für Bot-Nutzung.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

logger = logging.getLogger('bot.handlers.guide')


async def guide_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /anleitung Command.
    Zeigt kompakte Schnellanleitung.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} ({user.first_name}) executed /anleitung command")
    
    try:
        await context.bot.send_message(
            chat_id=chat_id,
            text="📱 *Schnellanleitung*\n\n"
                 "*📸 Party-Content* (1 Punkt)\n"
                 "→ Foto oder Video senden (ohne Caption)\n\n"
                 "*🎬 Film-Referenz* (20 Punkte)\n"
                 "→ Foto mit Caption: `Film: <Titel>`\n"
                 "→ Beispiel: `Film: Alien`\n\n"
                 "*👥 Team beitreten* (25 Punkte)\n"
                 "→ Command: `/team <6-stellige ID>`\n"
                 "→ Beispiel: `/team 358023`\n\n"
                 "*🧩 Puzzle lösen* (25 Punkte)\n"
                 "→ Screenshot mit Caption: `Puzzle`\n\n"
                 "━━━━━━━━━━━━━━━━━━━━━━\n"
                 "💡 *Weitere Befehle:*\n"
                 "/start - Einführung\n"
                 "/help - Ausführliche Hilfe\n"
                 "/punkte - Deine Punkte\n"
                 "/anleitung - Diese Anleitung\n\n"
                 "🎛️ *Oder nutze die Buttons unten!*",
            parse_mode='Markdown'
        )
        
        logger.debug(f"Guide sent to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in guide_command for user {user.id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
