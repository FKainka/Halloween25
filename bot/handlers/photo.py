"""
Foto-Upload Handler
Verarbeitet hochgeladene Fotos mit Caption-Erkennung.
"""

from telegram import Update
from telegram.ext import ContextTypes
import re
import logging

from database.db import db
from database.crud import (
    get_or_create_user, 
    create_submission, 
    has_recognized_film,
    add_easter_egg,
    has_solved_puzzle
)
from database.models import SubmissionType, SubmissionStatus
from services.photo_manager import photo_manager
from services.template_manager import template_manager
from services.ai_evaluator import ai_evaluator

logger = logging.getLogger('bot.handlers.photo')


async def photo_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für Foto-Uploads.
    Erkennt Caption-Befehle: "Film: <Titel>", "Puzzle"
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
        
        # Puzzle-Screenshot: "Puzzle"
        if caption_lower == 'puzzle':
            await handle_puzzle_submission(update, context, session, db_user, photo)
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
    photo
):
    """Verarbeitet Puzzle-Screenshot mit Caption 'Puzzle'."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob User in einem Team ist
    if not db_user.team_id:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Du musst zuerst einem Team beitreten!\n\n"
                 "👥 Nutze: `/team <Team-ID>`"
        )
        logger.info(f"User {user.id} tried to submit puzzle without being in a team")
        return
    
    # Prüfen ob User Puzzle bereits gelöst hat
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
            status=SubmissionStatus.APPROVED,
            caption="Puzzle"
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
    """Verarbeitet Film-Referenz Submission mit Caption 'Film: Titel'."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Film-Titel extrahieren: "Film: Matrix"
    match = re.search(r'film:\s*(.+)', caption, re.IGNORECASE)
    
    if not match:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte gib den Film-Titel an!\n\n"
                 "📝 Format: `Film: <Titel>`\n"
                 "Beispiel: `Film: Matrix`"
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
    
    try:
        # Foto herunterladen
        file = await context.bot.get_file(photo.file_id)
        photo_bytes = await file.download_as_bytearray()
        
        # Submission erstellen (PENDING bis KI bewertet hat)
        submission = create_submission(
            session=session,
            user_id=db_user.id,
            submission_type=SubmissionType.FILM_REFERENCE,
            photo_file_id=photo.file_id,
            caption=caption,
            film_title=film_title,
            points_awarded=0,  # Noch keine Punkte
            status=SubmissionStatus.PENDING
        )
        
        # Foto lokal speichern (brauchen wir für KI-Analyse)
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
        
        # "Wird analysiert..." Nachricht
        processing_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🤖 Analysiere deine Referenz zu \"{film_title}\"...\n\n"
                 f"Dies kann bis zu 10 Sekunden dauern."
        )
        
        # KI-Bewertung durchführen
        is_approved, confidence, reasoning, ai_response = ai_evaluator.evaluate_film_reference(
            photo_path=photo_path,
            film_title=film_title
        )
        
        # Submission aktualisieren
        if is_approved:
            submission.status = SubmissionStatus.APPROVED
            submission.points_awarded = 20
            submission.ai_evaluation = str(ai_response)
            
            # Easter Egg hinzufügen
            add_easter_egg(session, db_user.id, film_title)
            
            session.commit()
            
            # Erfolgs-Nachricht
            response = template_manager.render_film_approved(
                first_name=user.first_name or "Reisender",
                film_title=film_title,
                points=20,
                total_points=db_user.total_points,
                ai_reasoning=f"🎯 Confidence: {confidence}%\n\n{reasoning}"
            )
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=response
            )
            
            logger.info(
                f"Film reference APPROVED for user {user.id}: {film_title} "
                f"(+20 points) | Confidence: {confidence}%"
            )
            
        else:
            # KI hat Referenz nicht erkannt
            submission.status = SubmissionStatus.REJECTED
            submission.ai_evaluation = str(ai_response)
            session.commit()
            
            # Ablehnungs-Nachricht
            response = template_manager.render_film_rejected(
                first_name=user.first_name or "Reisender",
                film_title=film_title,
                reason=f"🤖 Confidence: {confidence}%\n\n{reasoning}\n\n"
                       f"💡 Tipp: Die Referenz muss eindeutig erkennbar sein!"
            )
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=response
            )
            
            logger.info(
                f"Film reference REJECTED for user {user.id}: {film_title} "
                f"| Confidence: {confidence}%"
            )
        
    except Exception as e:
        logger.error(f"Error processing film submission: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Fehler beim Verarbeiten der Film-Referenz. Bitte versuche es erneut."
        )

