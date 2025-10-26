"""
Admin Commands für den Halloween Bot
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
import json

from database.db import Database
from database import crud
from database.models import SubmissionType, SubmissionStatus
from config import config

logger = logging.getLogger('bot.handlers.admin')


async def admin_help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt ausführliche Admin-Hilfe mit allen Befehlen und Beispielen.
    
    Usage: /admin_help
    """
    user = update.effective_user
    
    # Prüfen ob User Admin ist
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    help_text = """🔧 **Admin-Befehle Hilfe**

**Übersicht:**
• `/admin` - Admin-Hauptmenü
• `/help_admin` - Diese Hilfe anzeigen

**Spieler-Verwaltung:**
• `/players` - Liste aller Spieler mit Punkten
• `/player <telegram_id>` - Details zu einem Spieler
• `/points <telegram_id> <punkte> <grund>` - Punkte manuell vergeben/abziehen

**Team-Verwaltung:**
• `/teams` - Übersicht aller Teams mit Mitgliedern

**Statistiken:**
• `/stats` - Party-Statistiken (Spieler, Submissions, Top 3)
• `/eastereggs` (oder `/films`) - Alle erkannten Filme

**Beispiele:**
```
/player 657163418
/points 657163418 50 Bonus für Kostüm
/points 657163418 -10 Regelverstoss
/stats
/teams
```

**Hinweise:**
• Alle Punkteänderungen werden im AdminLog protokolliert
• Telegram-IDs findest du mit /players
• Negative Punkte zum Abziehen verwenden
• Alle Commands funktionieren auch mit `admin_` Präfix"""
    
    await update.message.reply_text(help_text, parse_mode='Markdown')


async def admin_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Hauptmenü für Admins.
    Zeigt verfügbare Admin-Commands.
    
    Usage: /admin
    """
    user = update.effective_user
    
    # Prüfen ob User Admin ist
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    admin_menu = """
🔧 **ADMIN-MENÜ**

**Hilfe:**
/help_admin - Ausführliche Hilfe mit Beispielen

**Spieler-Verwaltung:**
/players - Alle Spieler anzeigen
/player <ID> - Details zu einem Spieler
/points <user_id> <punkte> <grund> - Punkte vergeben/abziehen

**Team & Stats:**
/teams - Alle Teams anzeigen
/stats - Party-Statistiken
/eastereggs (oder /films) - Erkannte Filme

━━━━━━━━━━━━━━━━━━━━━━
Du bist eingeloggt als Admin.
💡 Tipp: Alle Commands funktionieren auch mit admin_ Präfix
"""
    
    await update.message.reply_text(admin_menu, parse_mode='Markdown')
    logger.info(f"Admin {user.id} accessed admin menu")


async def admin_players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt alle Spieler mit ihren Punkten.
    
    Usage: /admin_players
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    db = Database()
    with db.get_session() as session:
        users = session.query(crud.User).order_by(crud.User.total_points.desc()).all()
        
        if not users:
            await update.message.reply_text("Noch keine Spieler registriert.")
            return
        
        message = "👥 **ALLE SPIELER**\n\n"
        
        for i, u in enumerate(users, 1):
            team_info = ""
            if u.team_id:
                team = session.query(crud.Team).filter_by(team_id=u.team_id).first()
                team_info = f" | Team: {team.film_title}" if team else ""
            
            message += f"{i}. **{u.first_name}** (@{u.username or 'N/A'})\n"
            message += f"   ID: `{u.telegram_id}` | Punkte: **{u.total_points}**{team_info}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} viewed all players")


async def admin_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt Details zu einem bestimmten Spieler.
    
    Usage: /admin_player <telegram_id>
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    if not context.args or len(context.args) != 1:
        await update.message.reply_text(
            "❌ Ungültiges Format!\n\n"
            "Nutze: /admin_player <telegram_id>"
        )
        return
    
    telegram_id = int(context.args[0])
    
    db = Database()
    with db.get_session() as session:
        player = session.query(crud.User).filter_by(telegram_id=telegram_id).first()
        
        if not player:
            await update.message.reply_text(f"❌ Spieler mit ID {telegram_id} nicht gefunden.")
            return
        
        # Submissions zählen
        submissions = session.query(crud.Submission).filter_by(user_id=player.id).all()
        party_photos = sum(1 for s in submissions if s.submission_type == SubmissionType.PARTY_PHOTO)
        films = sum(1 for s in submissions if s.submission_type == SubmissionType.FILM_REFERENCE)
        
        # Team-Info
        team_info = "Kein Team"
        if player.team_id:
            team = session.query(crud.Team).filter_by(team_id=player.team_id).first()
            team_info = f"{team.film_title} (ID: {player.team_id})"
        
        # Easter Eggs
        easter_eggs = session.query(crud.EasterEgg).filter_by(user_id=player.id).all()
        films_list = ", ".join([e.film_title for e in easter_eggs]) if easter_eggs else "Keine"
        
        message = f"""
👤 **SPIELER-DETAILS**

**Name:** {player.first_name} {player.last_name or ''}
**Username:** @{player.username or 'N/A'}
**Telegram-ID:** `{player.telegram_id}`
**DB-ID:** {player.id}

**📊 STATISTIKEN:**
Gesamt-Punkte: **{player.total_points}**
Party-Fotos: {party_photos}
Film-Referenzen: {films}
Team: {team_info}

**🎬 Erkannte Filme:**
{films_list}

**📅 Registriert:** {player.created_at.strftime('%d.%m.%Y %H:%M')}
"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} viewed player {telegram_id}")


async def admin_teams_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt alle Teams mit Mitgliedern.
    
    Usage: /admin_teams
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    db = Database()
    with db.get_session() as session:
        teams = session.query(crud.Team).all()
        
        message = "🎬 **ALLE TEAMS**\n\n"
        
        for team in teams:
            members = session.query(crud.User).filter_by(team_id=team.team_id).all()
            member_count = len(members)
            
            message += f"**{team.film_title}** (ID: `{team.team_id}`)\n"
            message += f"Charaktere: {team.character_1} & {team.character_2}\n"
            message += f"Mitglieder: {member_count}\n"
            
            if members:
                member_names = ", ".join([m.first_name for m in members])
                message += f"→ {member_names}\n"
            
            message += "\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} viewed all teams")


async def admin_stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt Party-Statistiken.
    
    Usage: /admin_stats
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    db = Database()
    with db.get_session() as session:
        # Gesamt-Statistiken
        total_users = session.query(crud.User).count()
        total_submissions = session.query(crud.Submission).count()
        total_points = session.query(crud.User).with_entities(
            crud.User.total_points
        ).all()
        sum_points = sum([p[0] for p in total_points])
        
        # Submissions nach Typ
        party_photos = session.query(crud.Submission).filter_by(
            submission_type=SubmissionType.PARTY_PHOTO
        ).count()
        films = session.query(crud.Submission).filter_by(
            submission_type=SubmissionType.FILM_REFERENCE
        ).count()
        team_joins = session.query(crud.Submission).filter_by(
            submission_type=SubmissionType.TEAM_JOIN
        ).count()
        puzzles = session.query(crud.Submission).filter_by(
            submission_type=SubmissionType.PUZZLE
        ).count()
        
        # Teams mit Mitgliedern
        teams_with_members = session.query(crud.User.team_id).filter(
            crud.User.team_id.isnot(None)
        ).distinct().count()
        
        # Top 3 Spieler
        top_users = session.query(crud.User).order_by(
            crud.User.total_points.desc()
        ).limit(3).all()
        
        message = f"""
📊 **PARTY-STATISTIKEN**

**Gesamt:**
👥 Spieler: {total_users}
📸 Submissions: {total_submissions}
⭐ Gesamt-Punkte: {sum_points}

**Submissions nach Typ:**
📷 Party-Fotos: {party_photos}
🎬 Film-Referenzen: {films}
👫 Team-Beitritte: {team_joins}
🧩 Puzzles gelöst: {puzzles}

**Teams:**
Aktive Teams: {teams_with_members}

**🏆 TOP 3:**
"""
        
        for i, u in enumerate(top_users, 1):
            emoji = ["🥇", "🥈", "🥉"][i-1]
            message += f"{emoji} {u.first_name}: **{u.total_points}** Punkte\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} viewed stats")


async def admin_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vergibt/Entzieht Punkte manuell.
    
    Usage: /admin_points <telegram_id> <points> <reason>
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    if not context.args or len(context.args) < 3:
        await update.message.reply_text(
            "❌ Ungültiges Format!\n\n"
            "Nutze: /admin_points <telegram_id> <points> <reason>\n"
            "Beispiel: /admin_points 123456789 10 Bonus für cooles Kostüm"
        )
        return
    
    telegram_id = int(context.args[0])
    points = int(context.args[1])
    reason = " ".join(context.args[2:])
    
    db = Database()
    with db.get_session() as session:
        player = session.query(crud.User).filter_by(telegram_id=telegram_id).first()
        
        if not player:
            await update.message.reply_text(f"❌ Spieler mit ID {telegram_id} nicht gefunden.")
            return
        
        # Punkte vergeben
        old_points = player.total_points
        player.total_points += points
        
        # Admin-Log erstellen (details als JSON-String)
        details_dict = {
            "points": points, 
            "reason": reason, 
            "old_total": old_points, 
            "new_total": player.total_points
        }
        
        admin_log = crud.AdminLog(
            admin_id=user.id,
            action="MANUAL_POINTS",
            target_user_id=telegram_id,
            details=json.dumps(details_dict)  # Als JSON-String speichern
        )
        session.add(admin_log)
        session.commit()
        
        message = f"""
✅ **PUNKTE ANGEPASST**

Spieler: {player.first_name}
Alte Punkte: {old_points}
Anpassung: {points:+d}
Neue Punkte: **{player.total_points}**

Grund: {reason}
"""
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} adjusted points for user {telegram_id}: {points:+d} ({reason})")


async def admin_eastereggs_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt alle erkannten Filme.
    
    Usage: /admin_eastereggs
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    db = Database()
    with db.get_session() as session:
        easter_eggs = session.query(crud.EasterEgg).all()
        
        if not easter_eggs:
            await update.message.reply_text("Noch keine Filme erkannt.")
            return
        
        # Gruppiere nach Film
        films_dict = {}
        for egg in easter_eggs:
            if egg.film_title not in films_dict:
                films_dict[egg.film_title] = []
            
            user_obj = session.query(crud.User).filter_by(id=egg.user_id).first()
            films_dict[egg.film_title].append(user_obj.first_name)
        
        message = "🎬 **ERKANNTE FILME**\n\n"
        
        for film, users in sorted(films_dict.items()):
            message += f"**{film}** ({len(users)}x)\n"
            message += f"→ {', '.join(users)}\n\n"
        
        await update.message.reply_text(message, parse_mode='Markdown')
        logger.info(f"Admin {user.id} viewed easter eggs")
