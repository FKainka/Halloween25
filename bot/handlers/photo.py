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
    update_submission_status,
    has_recognized_film,
    add_easter_egg,
    has_solved_puzzle,
    get_team_by_id
)
from database.models import SubmissionType, SubmissionStatus
from services.photo_manager import photo_manager
from services.template_manager import template_manager
from services.ai_evaluator import ai_evaluator
from utils.yaml_loader import universe_loader

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
            category='party',
            user_name=user.first_name
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
                 "👥 Nutze: /team <Team-ID>\n\n"
                 "💡 Addiere deine Charakter-ID mit der deines Partners.\n"
                 "Beispiel: /team 358023"
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
    
    # Team-Informationen holen
    team = get_team_by_id(session, db_user.team_id)
    if not team:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Fehler: Team nicht gefunden!"
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
            submission_type=SubmissionType.PUZZLE,
            photo_file_id=photo.file_id,
            points_awarded=0,  # Noch keine Punkte
            status=SubmissionStatus.PENDING,
            caption="Puzzle"
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
        
        # "Wird analysiert..." Nachricht
        processing_msg = await context.bot.send_message(
            chat_id=chat_id,
            text=f"🤖 Prüfe dein Puzzle zu \"{team.film_title}\"...\n\n"
                 f"Dies kann bis zu 10 Sekunden dauern."
        )
        
        # Team-Daten aus YAML holen für Poster-URLs
        teams_data = universe_loader.get_teams()
        team_data = next((t for t in teams_data if t['team_id'] == db_user.team_id), None)
        poster_urls = team_data.get('posters', []) if team_data else []
        
        # KI-Bewertung durchführen (async für bessere Performance)
        is_approved, confidence, reasoning, ai_response = await ai_evaluator.evaluate_puzzle_poster_async(
            photo_path=photo_path,
            film_title=team.film_title,
            poster_urls=poster_urls
        )
        
        # Submission aktualisieren
        if is_approved:
            update_submission_status(
                session=session,
                submission_id=submission.id,
                status=SubmissionStatus.APPROVED,
                points_awarded=25,
                ai_evaluation=str(ai_response)
            )
            
            # User-Punkte neu laden
            session.refresh(db_user)
            
            # Erfolgs-Nachricht
            response = template_manager.render_puzzle_completed(
                first_name=user.first_name or "Reisender",
                points=25,
                total_points=db_user.total_points
            )
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=response + f"\n\n🎯 Confidence: {confidence}%\n{reasoning}"
            )
            
            logger.info(f"Puzzle APPROVED for user {user.id}: {team.film_title} (+25 points) | Confidence: {confidence}%")
            
        else:
            # KI hat Puzzle nicht als gültig erkannt
            update_submission_status(
                session=session,
                submission_id=submission.id,
                status=SubmissionStatus.REJECTED,
                ai_evaluation=str(ai_response)
            )
            
            # Ablehnungs-Nachricht
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=f"❌ Puzzle konnte nicht verifiziert werden\n\n"
                     f"🤖 Confidence: {confidence}%\n\n"
                     f"{reasoning}\n\n"
                     f"💡 **Wichtig:**\n"
                     f"- Puzzle muss vollständig gelöst sein\n"
                     f"- Muss ein Filmplakat zu \"{team.film_title}\" zeigen\n"
                     f"- Film-Titel oder eindeutige Elemente müssen erkennbar sein"
            )
            
            logger.info(f"Puzzle REJECTED for user {user.id}: {team.film_title} | Confidence: {confidence}%")
        
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
            film_title=film_title,
            user_name=user.first_name
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
        
        # Film-Daten aus YAML holen für Easter Egg Beschreibung
        teams_data = universe_loader.get_teams()
        film_data = next((t for t in teams_data if t['film_title'].lower() == film_title.lower()), None)
        easter_egg_description = None
        if film_data and film_data.get('easter_egg'):
            easter_egg = film_data['easter_egg']
            easter_egg_description = (
                f"Easter Egg: {easter_egg.get('name', '')}\n"
                f"Beschreibung: {easter_egg.get('description', '')}"
            )
        
        # KI-Bewertung durchführen (async für bessere Performance)
        is_approved, confidence, reasoning, ai_response = await ai_evaluator.evaluate_film_reference_async(
            photo_path=photo_path,
            film_title=film_title,
            easter_egg_description=easter_egg_description
        )
        
        # Submission aktualisieren
        if is_approved:
            update_submission_status(
                session=session,
                submission_id=submission.id,
                status=SubmissionStatus.APPROVED,
                points_awarded=20,
                ai_evaluation=str(ai_response)
            )
            
            # Easter Egg hinzufügen
            add_easter_egg(session, db_user.id, film_title)
            
            # User-Punkte neu laden
            session.refresh(db_user)
            
            # Referenz-Typ aus AI Response
            reference_type = ai_response.get('reference_type', 'unknown')
            type_emoji = {
                'easter_egg': '🥚',
                'scene': '🎬',
                'screen_capture': '📺',
                'poster': '🎭',
                'costume': '👗',
                'prop': '🔧',
                'other': '✨'
            }.get(reference_type, '✨')
            
            # Erfolgs-Nachricht
            response = template_manager.render_film_approved(
                first_name=user.first_name or "Reisender",
                film_title=film_title,
                points=20,
                total_points=db_user.total_points,
                ai_reasoning=f"{type_emoji} Typ: {reference_type}\n🎯 Confidence: {confidence}%\n\n{reasoning}"
            )
            
            await context.bot.edit_message_text(
                chat_id=chat_id,
                message_id=processing_msg.message_id,
                text=response
            )
            
            logger.info(
                f"Film reference APPROVED for user {user.id}: {film_title} "
                f"(+20 points) | Type: {reference_type} | Confidence: {confidence}%"
            )
            
        else:
            # KI hat Referenz nicht erkannt
            update_submission_status(
                session=session,
                submission_id=submission.id,
                status=SubmissionStatus.REJECTED,
                ai_evaluation=str(ai_response)
            )
            
            # Ablehnungs-Nachricht
            response = template_manager.render_film_rejected(
                first_name=user.first_name or "Reisender",
                film_title=film_title,
                reason=f"🤖 Confidence: {confidence}%\n\n{reasoning}\n\n"
                       f"💡 **Tipps für gültige Referenzen:**\n"
                       f"- 🥚 Easter Egg (spezifischer Gegenstand aus dem Film)\n"
                       f"- 🎬 Nachgestellte Szene\n"
                       f"- 📺 Foto vom laufenden Film\n"
                       f"- 🎭 Filmplakat\n"
                       f"- 👗 Kostüm/Verkleidung als Charakter\n"
                       f"- 🔧 Ikonische Requisite"
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

