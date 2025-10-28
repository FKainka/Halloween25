"""
Handler für /team Command - Team-Beitritt
"""
from telegram import Update
from telegram.ext import ContextTypes
import re
import logging

from database.db import Database
from database import crud
from database.models import SubmissionType
from services.template_manager import template_manager

logger = logging.getLogger('bot.handlers.team')


async def team_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Handler für /team <ID> Command.
    User tritt einem Team bei durch Eingabe der Team-ID.
    
    Usage: /team 480514
    """
    user = update.effective_user
    
    try:
        # Team-ID aus Command-Argumenten extrahieren
        if not context.args or len(context.args) != 1:
            await update.message.reply_text(
                "❌ Ungültiges Format!\n\n"
                "📝 Nutze: /team <Team-ID>\n"
                "Beispiel: /team 480514\n\n"
                "💡 Die Team-ID erhältst du, indem du deine Charakter-ID "
                "mit der deines Partners addierst.\n"
                "Beispiel: 123456 + 234567 = 358023"
            )
            return
        
        team_id_str = context.args[0]
        
        # Validierung: Muss 6 Ziffern sein
        if not re.match(r'^\d{6}$', team_id_str):
            await update.message.reply_text(
                "❌ Die Team-ID muss genau 6 Ziffern haben!\n\n"
                f"Du hast eingegeben: {team_id_str}\n\n"
                "💡 Addiere deine Charakter-ID mit der deines Partners.\n"
                "Beispiel: 123456 + 234567 = 358023"
            )
            return
        
        team_id = int(team_id_str)
        
        logger.info(f"User {user.id} ({user.username}) attempting to join team {team_id}")
        
        # Database-Session
        db = Database()
        with db.get_session() as session:
            # User abrufen/erstellen
            db_user = crud.get_or_create_user(
                session,
                telegram_id=user.id,
                username=user.username or "",
                first_name=user.first_name or "User",
                last_name=user.last_name or ""
            )
            
            # Prüfen ob User bereits in einem Team ist
            if db_user.team_id is not None:
                team = session.query(crud.Team).filter_by(team_id=db_user.team_id).first()
                await update.message.reply_text(
                    f"⚠️ Du bist bereits im Team **{team.film_title}**!\n\n"
                    f"Team-ID: {db_user.team_id}\n"
                    f"Charaktere: {team.character_1} & {team.character_2}\n\n"
                    "Du kannst nur einem Team beitreten.",
                    parse_mode='Markdown'
                )
                logger.info(f"User {user.id} already in team {db_user.team_id}")
                return
            
            # Team suchen
            team = session.query(crud.Team).filter_by(team_id=team_id).first()
            
            if not team:
                await update.message.reply_text(
                    f"❌ Team-ID **{team_id}** wurde nicht gefunden!\n\n"
                    "🔍 Mögliche Ursachen:\n"
                    "• Falsche Berechnung der Charakter-IDs\n"
                    "• Tippfehler bei der Eingabe\n\n"
                    "💡 Tipp: Addiere deine Charakter-ID mit der ID "
                    "deines Partners und versuche es erneut.\n"
                    "Beispiel: 123456 + 234567 = 358023",
                    parse_mode='Markdown'
                )
                logger.warning(f"User {user.id} tried invalid team_id: {team_id}")
                return
            
            # Team-Beitritt durchführen
            success = crud.join_team(session, db_user.id, str(team_id))
            
            if success:
                # Submission erstellen für Punkte
                crud.create_submission(
                    session,
                    user_id=db_user.id,
                    submission_type=SubmissionType.TEAM_JOIN,
                    points_awarded=25
                )
                
                # Erfolgs-Nachricht mit Template
                message = template_manager.render_team_joined(
                    first_name=user.first_name or "User",
                    team_name=team.film_title,
                    points=25,
                    puzzle_link=team.puzzle_link if team.puzzle_link else "Kein Puzzle verfügbar"
                )
                
                await update.message.reply_text(message, parse_mode='Markdown')
                
                logger.info(f"User {user.id} joined team {team_id} ({team.film_title}). Points: 25")
            else:
                await update.message.reply_text(
                    "❌ Fehler beim Team-Beitritt. Bitte versuche es später erneut."
                )
                logger.error(f"Failed to join team {team_id} for user {user.id}")
    
    except Exception as e:
        logger.error(f"Error in team_command for user {user.id}: {e}", exc_info=True)
        await update.message.reply_text(
            "❌ Ein Fehler ist aufgetreten. Bitte versuche es später erneut."
        )
