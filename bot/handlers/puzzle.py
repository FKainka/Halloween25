"""
/puzzle Command Handler
Verarbeitet Puzzle-Screenshot Submissions.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from database.db import db
from database.crud import (
    get_or_create_user, 
    create_submission, 
    has_solved_puzzle
)
from database.models import SubmissionType, SubmissionStatus
from services.photo_manager import photo_manager
from services.template_manager import template_manager

logger = logging.getLogger('bot.handlers.puzzle')


async def puzzle_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /puzzle Command mit Screenshot-Anhang.
    User muss bereits einem Team beigetreten sein.
    
    Usage: 
    - /puzzle (mit angehängtem Screenshot)
    - Screenshot senden mit Caption: /puzzle
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob Foto vorhanden ist
    if not update.message.photo:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte hänge einen Screenshot des gelösten Puzzles an!\n\n"
                 "📝 So geht's:\n"
                 "1. Puzzle lösen\n"
                 "2. Screenshot machen\n"
                 "3. Screenshot mit /puzzle senden\n\n"
                 "⚠️ Du musst zuerst einem Team beitreten!"
        )
        return
    
    logger.info(f"User {user.id} submitted puzzle screenshot")
    
    with db.get_session() as session:
        # User registrieren/holen
        db_user = get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Prüfen ob User in einem Team ist
        if not db_user.team_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Du musst zuerst einem Team beitreten!\n\n"
                     "👥 Nutze: /team <Team-ID>\n"
                     "oder den Button '👥 Team beitreten'"
            )
            logger.info(f"User {user.id} tried to submit puzzle without being in a team")
            return
        
        # Prüfen ob User Puzzle bereits gelöst hat
        if has_solved_puzzle(session, db_user.id):
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Du hast das Puzzle bereits gelöst!\n\n"
                     "Du kannst nur einmal Punkte für das Puzzle erhalten."
            )
            logger.info(f"User {user.id} tried to submit duplicate puzzle")
            return
        
        try:
            # Foto herunterladen
            photo = update.message.photo[-1]  # Größtes Foto
            file = await context.bot.get_file(photo.file_id)
            photo_bytes = await file.download_as_bytearray()
            
            # Submission erstellen (automatisch approved)
            submission = create_submission(
                session=session,
                user_id=db_user.id,
                submission_type=SubmissionType.PUZZLE,
                photo_file_id=photo.file_id,
                points_awarded=25,
                status=SubmissionStatus.APPROVED,
                caption=f"Team: {db_user.team_id}"
            )
            
            # Foto lokal speichern
            photo_path, thumbnail_path = photo_manager.save_photo(
                photo_bytes=bytes(photo_bytes),
                user_id=user.id,
                submission_id=submission.id,
                category='puzzles',
                user_name=user.first_name
            )
            
            # Pfade in Submission aktualisieren
            submission.photo_path = photo_path
            submission.thumbnail_path = thumbnail_path
            session.commit()
            
            # Bestätigung senden
            response = template_manager.render_puzzle_completed(
                first_name=user.first_name or "Reisender",
                points=25,
                total_points=db_user.total_points
            )
            
            await context.bot.send_message(chat_id=chat_id, text=response)
            
            logger.info(f"Puzzle completed by user {user.id}: +25 points")
            
        except Exception as e:
            logger.error(f"Error processing puzzle screenshot: {e}", exc_info=True)
            await context.bot.send_message(
                chat_id=chat_id,
                text="❌ Fehler beim Verarbeiten des Screenshots. Bitte versuche es erneut."
            )
