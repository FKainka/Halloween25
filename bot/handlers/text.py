"""
Text-Message Handler
Verarbeitet Text-Nachrichten (z.B. Team-Beitritt).
"""

from telegram import Update
from telegram.ext import ContextTypes
import re
import logging

from database.db import db
from database.crud import get_or_create_user, create_submission, get_team_by_id, join_team
from database.models import SubmissionType, SubmissionStatus
from services.template_manager import template_manager

logger = logging.getLogger('bot.handlers.text')


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für Text-Nachrichten.
    Erkennt: Team: <ID>
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not update.message or not update.message.text:
        return
    
    text = update.message.text.strip()
    text_lower = text.lower()
    
    logger.debug(f"User {user.id} sent text: '{text}'")
    
    # Team-Beitritt: "Team: 123456"
    if text_lower.startswith('team:'):
        await handle_team_join(update, context, text)
    else:
        # Andere Texte ignorieren (keine Fehlermeldung)
        pass


async def handle_team_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    text: str
):
    """Verarbeitet Team-Beitritt via Text."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Team-ID extrahieren: "Team: 123456"
    match = re.search(r'team:\s*(\d{6})', text, re.IGNORECASE)
    
    if not match:
        await context.bot.send_message(
            chat_id=chat_id,
            text=template_manager.render_error('team_invalid', 'Format: Team: 123456')
        )
        return
    
    team_id = match.group(1)
    
    logger.info(f"User {user.id} attempting to join team {team_id}")
    
    with db.get_session() as session:
        # User registrieren/holen
        db_user = get_or_create_user(
            session,
            telegram_id=user.id,
            username=user.username,
            first_name=user.first_name,
            last_name=user.last_name
        )
        
        # Team in DB suchen
        team = get_team_by_id(session, team_id)
        
        if not team:
            await context.bot.send_message(
                chat_id=chat_id,
                text=template_manager.render_error('team_invalid', f'Team-ID {team_id} nicht gefunden')
            )
            logger.warning(f"Invalid team ID: {team_id} from user {user.id}")
            return
        
        # Prüfen ob User bereits in Team ist
        if db_user.team_id:
            await context.bot.send_message(
                chat_id=chat_id,
                text=template_manager.render_error('team_already_joined')
            )
            return
        
        # User tritt Team bei
        success = join_team(session, db_user.id, team_id)
        
        if not success:
            await context.bot.send_message(
                chat_id=chat_id,
                text=template_manager.render_error('team_already_joined')
            )
            return
        
        # Punkte vergeben für Team-Beitritt
        create_submission(
            session=session,
            user_id=db_user.id,
            submission_type=SubmissionType.TEAM_JOIN,
            points_awarded=25,
            status=SubmissionStatus.APPROVED,
            caption=f"Team: {team_id}"
        )
        
        # Bestätigung mit Puzzle-Link senden
        response = template_manager.render_team_joined(
            first_name=user.first_name or "Reisender",
            team_name=team.film_title,
            points=25,
            puzzle_link=team.puzzle_link
        )
        
        await context.bot.send_message(chat_id=chat_id, text=response)
        
        logger.info(f"User {user.id} joined team {team_id} ({team.film_title}): +25 points")
