"""
/film Command Handler
Verarbeitet Film-Referenz Submissions mit Foto-Anhang.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from database.db import db
from database.crud import get_or_create_user, create_submission, has_recognized_film, add_easter_egg
from database.models import SubmissionType, SubmissionStatus
from services.photo_manager import photo_manager
from services.template_manager import template_manager
from services.ai_evaluator import ai_evaluator

logger = logging.getLogger('bot.handlers.film')


async def film_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /film <Filmtitel> Command mit Foto-Anhang.
    
    Usage: 
    - /film Matrix (mit angehängtem Foto)
    - Foto senden mit Caption: /film Matrix
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob Foto vorhanden ist
    if not update.message.photo:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte hänge ein Foto an!\n\n"
                 "📝 So geht's:\n"
                 "1. Foto auswählen\n"
                 "2. Als Caption eingeben: /film <Filmtitel>\n"
                 "3. Senden\n\n"
                 "Beispiel: /film Matrix"
        )
        return
    
    # Film-Titel aus Command-Argumenten extrahieren
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Bitte gib den Film-Titel an!\n\n"
                 "📝 Format: /film <Filmtitel>\n"
                 "Beispiel: /film Matrix"
        )
        return
    
    film_title = ' '.join(context.args).strip()
    
    if not film_title:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Film-Titel darf nicht leer sein!"
        )
        return
    
    logger.info(f"User {user.id} submitted film reference: '{film_title}'")
    
    with db.get_session() as session:
        # User registrieren/holen
        db_user = get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Prüfen ob User diesen Film bereits submitted hat
        if has_recognized_film(session, db_user.id, film_title):
            await context.bot.send_message(
                chat_id=chat_id,
                text=template_manager.render_error(
                    'film_already_submitted',
                    f'Du hast "{film_title}" bereits erkannt!'
                )
            )
            logger.info(f"User {user.id} tried to submit duplicate film: {film_title}")
            return
        
        try:
            # Foto herunterladen
            photo = update.message.photo[-1]  # Größtes Foto
            file = await context.bot.get_file(photo.file_id)
            photo_bytes = await file.download_as_bytearray()
            
            # Submission erstellen (PENDING bis KI bewertet hat)
            submission = create_submission(
                session=session,
                user_id=db_user.id,
                submission_type=SubmissionType.FILM_REFERENCE,
                photo_file_id=photo.file_id,
                caption=f"/film {film_title}",
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
