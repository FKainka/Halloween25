"""
/punkte Command Handler
Zeigt Punktestand und Statistiken des Users.
"""

from telegram import Update
from telegram.ext import ContextTypes
import logging

from database.db import db
from database.crud import get_or_create_user, get_user_stats, get_top_players, get_top_teams
from services.template_manager import template_manager

logger = logging.getLogger('bot.handlers.points')


async def points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /punkte Command.
    Zeigt detaillierte Punkteübersicht.
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    logger.info(f"User {user.id} ({user.first_name}) executed /punkte command")
    
    try:
        with db.get_session() as session:
            # User holen
            db_user = get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name
            )
            
            # Statistiken holen
            stats = get_user_stats(session, db_user.id)
            
            # Top-Spieler und -Teams holen
            top_players = get_top_players(session, limit=3)
            top_teams = get_top_teams(session, limit=3)
            
            # Punkte-Übersicht aus Template rendern
            points_text = template_manager.render_points(
                first_name=user.first_name or "Reisender",
                total_points=stats['total_points'],
                party_photos_count=stats['party_photos_count'],
                party_points=stats['party_points'],
                film_submitted=stats['film_submitted'],
                film_approved=stats['film_approved'],
                film_count=stats['film_count'],
                film_points=stats['film_points'],
                team_points=stats['team_points'],
                puzzle_points=stats['puzzle_points'],
                team_name=stats['team_name'],
                recognized_films=stats['recognized_films'],
                ranking=stats['ranking'],
                total_users=stats['total_users'],
                top_players=top_players,
                top_teams=top_teams
            )
            
            # Nachricht senden
            await context.bot.send_message(
                chat_id=chat_id,
                text=points_text
            )
            
            logger.debug(f"Points overview sent to user {user.id}")
        
    except Exception as e:
        logger.error(f"Error in points_command for user {user.id}: {e}", exc_info=True)
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
