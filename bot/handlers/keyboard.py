"""
Keyboard Button Handler
Verarbeitet Nachrichten von Custom Keyboard Buttons.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from handlers.help import help_command
from handlers.points import points_command

logger = logging.getLogger('bot.handlers.keyboard')


async def keyboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für Custom Keyboard Button-Klicks.
    Routet Button-Text zu entsprechenden Commands.
    """
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    user = update.effective_user
    
    logger.debug(f"User {user.id} clicked keyboard button: '{text}'")
    
    # Button-Text zu Command mapping
    if text == "🏆 Meine Punkte":
        await points_command(update, context)
        
    elif text == "❓ Hilfe":
        await help_command(update, context)
        
    elif text == "ℹ️ Anleitung":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📱 *Schnellanleitung*\n\n"
                 "*📸 Partyfoto* (1 Punkt)\n"
                 "→ Foto senden (ohne Caption)\n\n"
                 "*🎬 Film-Referenz* (20 Punkte)\n"
                 "→ Foto mit Caption: `Film: <Titel>`\n"
                 "→ Beispiel: `Film: Matrix`\n\n"
                 "*👥 Team beitreten* (25 Punkte)\n"
                 "→ Command: `/team <6-stellige ID>`\n"
                 "→ Beispiel: `/team 480514`\n\n"
                 "*🧩 Puzzle lösen* (25 Punkte)\n"
                 "→ Screenshot mit Caption: `Puzzle`\n\n"
                 "💡 *Tipp:* Tippe `/` um alle Commands zu sehen!",
            parse_mode='Markdown'
        )
    
    else:
        # Anderer Text - ignorieren oder an text_handler weiterleiten
        pass
