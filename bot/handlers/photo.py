"""
Foto-Upload Handler
Verarbeitet hochgeladene Fotos und erkennt Caption-Befehle.
"""

from telegram import Update
from telegram.ext import ContextTypes
import re
import logging

from database.db import db
from database.crud import get_or_create_user, create_submission, get_team_by_id, join_team, has_recognized_film
from database.models import SubmissionType, SubmissionStatus
from services.photo_manager import photo_manager
from services.template_manager import template_manager
from config import config

logger = logging.getLogger('bot.handlers.photo')


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für Foto-Uploads.
    Erkennt: Team: (für Puzzle), Film: oder allgemeines Partyfoto.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Foto-Objekt holen
    if not update.message or not update.message.photo:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte sende ein Foto!"
        )
        return
    
    photo = update.message.photo[-1]  # Größtes Foto
    caption = update.message.caption or ""
    
    logger.info(f"User {user.id} uploaded photo with caption: '{caption}'")
    
    with db.get_session() as session:
        # User registrieren/holen
        db_user = get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Caption parsen
        caption_lower = caption.lower().strip()
        
        # Puzzle-Screenshot: "Team: 123456" (User muss bereits im Team sein)
        if caption_lower.startswith('team:'):
            await handle_puzzle_submission(update, context, session, db_user, photo, caption)
            return
        
        # Film-Referenz: "Film: Matrix"
        elif caption_lower.startswith('film:'):
            await handle_film_submission(update, context, session, db_user, photo, caption)
            return
        
        # Allgemeines Partyfoto (kein Caption oder anderes)
        else:
            await handle_party_photo(update, context, session, db_user, photo)
            return


async def handle_party_photo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user,
    photo
):
    """Verarbeitet allgemeines Partyfoto."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    try:
        # Foto herunterladen
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        
        # Submission erstellen (für ID)
        submission = create_submission(
            session=session,
            user_id=db_user.id,
            submission_type=SubmissionType.PARTY_PHOTO,
            photo_file_id=photo.file_id,
            points_awarded=1,
            status=SubmissionStatus.APPROVED
        )
        
        # Foto lokal speichern
        photo_path, thumbnail_path = photo_manager.save_photo(
            photo_bytes=bytes(photo_bytes),
            user_id=user.id,
            submission_id=submission.id,
            category='party'
        )
        
        # Pfade in Submission aktualisieren
        submission.photo_path = photo_path
        submission.thumbnail_path = thumbnail_path
        session.commit()
        
        # Bestätigung senden
        response = template_manager.render_party_photo_thanks(
            first_name=user.first_name or "Reisender",
            points=1,
            total_points=db_user.total_points
        )
        
        await context.bot.send_message(chat_id=chat_id, text=response)
        
        logger.info(f"Party photo processed for user {user.id}: +1 point")
        
    except Exception as e:
        logger.error(f"Error processing party photo: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Fehler beim Verarbeiten des Fotos. Bitte versuche es erneut."
        )


async def handle_puzzle_submission(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user,
    photo,
    caption: str
):
    """Verarbeitet Puzzle-Screenshot (User muss bereits im Team sein)."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Team-ID extrahieren
    match = re.search(r'team:\s*(\d{6})', caption, re.IGNORECASE)
    
    if not match:
        await context.bot.send_message(
            chat_id=chat_id,
            text=template_manager.render_error('team_invalid', 'Format: Team: 123456')
        )
        return
    
    team_id = match.group(1)
    
    # Prüfen ob User in diesem Team ist
    if not db_user.team_id or db_user.team_id != team_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Du bist nicht in diesem Team! Trete zuerst mit 'Team: <ID>' (nur Text) bei."
        )
        return
    
    # Prüfen ob User Puzzle bereits gelöst hat
    from database.crud import has_solved_puzzle
    
    if has_solved_puzzle(session, db_user.id):
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Du hast das Puzzle bereits gelöst!"
        )
        return
    
    try:
        # Foto herunterladen
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        
        # Submission erstellen
        submission = create_submission(
            session=session,
            user_id=db_user.id,
            submission_type=SubmissionType.PUZZLE,
            photo_file_id=photo.file_id,
            points_awarded=25,
            status=SubmissionStatus.APPROVED
        )
        
        # Foto lokal speichern
        photo_path, thumbnail_path = photo_manager.save_photo(
            photo_bytes=bytes(photo_bytes),
            user_id=user.id,
            submission_id=submission.id,
            category='puzzles'
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


async def handle_film_submission(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    session,
    db_user,
    photo,
    caption: str
):
    """Verarbeitet Film-Referenz Submission."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Film-Titel extrahieren: "Film: Matrix"
    match = re.search(r'film:\s*(.+)', caption, re.IGNORECASE)
    
    if not match:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte gib den Film-Titel an: Film: <Titel>"
        )
        return
    
    film_title = match.group(1).strip()
    
    # Prüfen ob User diesen Film bereits submitted hat
    if has_recognized_film(session, db_user.id, film_title):
        await context.bot.send_message(
            chat_id=chat_id,
            text=template_manager.render_error(
                'film_already_submitted',
                f'Du hast "{film_title}" bereits erkannt!'
            )
        )
        return
    
    # TODO: Hier kommt später die KI-Bewertung
    # Für jetzt: Automatisch akzeptieren
    
    try:
        # Foto herunterladen
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        
        # Submission erstellen
        submission = create_submission(
            session=session,
            user_id=db_user.id,
            submission_type=SubmissionType.FILM_REFERENCE,
            photo_file_id=photo.file_id,
            caption=caption,
            film_title=film_title,
            points_awarded=20,
            status=SubmissionStatus.APPROVED
        )
        
        # Easter Egg hinzufügen
        from database.crud import add_easter_egg
        add_easter_egg(session, db_user.id, film_title)
        
        # Foto lokal speichern
        photo_path, thumbnail_path = photo_manager.save_photo(
            photo_bytes=bytes(photo_bytes),
            user_id=user.id,
            submission_id=submission.id,
            category='films',
            film_title=film_title
        )
        
        # Pfade in Submission aktualisieren
        submission.photo_path = photo_path
        submission.thumbnail_path = thumbnail_path
        session.commit()
        
        # Bestätigung senden
        response = template_manager.render_film_approved(
            first_name=user.first_name or "Reisender",
            film_title=film_title,
            points=20,
            total_points=db_user.total_points,
            ai_reasoning="Film-Referenz wurde erkannt! (KI-Bewertung folgt später)"
        )
        
        await context.bot.send_message(chat_id=chat_id, text=response)
        
        logger.info(f"Film reference accepted for user {user.id}: {film_title} (+20 points)")
        
    except Exception as e:
        logger.error(f"Error processing film submission: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Fehler beim Verarbeiten der Film-Referenz. Bitte versuche es erneut."
        )
