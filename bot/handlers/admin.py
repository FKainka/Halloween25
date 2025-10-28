"""
Admin Commands für den Halloween Bot
"""
from telegram import Update
from telegram.ext import ContextTypes
import logging
import json

from database.db import Database
from database import crud
from database.models import SubmissionType, SubmissionStatus, User, Submission, EasterEgg
from config import config
from services.ai_evaluator import ai_evaluator

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
    
    help_text = """🔧 Admin-Befehle Hilfe

Übersicht:
• /admin - Admin-Hauptmenü
• /help_admin - Diese Hilfe anzeigen

Spieler-Verwaltung:
• /players - Liste aller Spieler mit Punkten
• /player <id|name|@user> - Details zu einem Spieler
• /points <telegram_id> <punkte> <grund> - Punkte manuell vergeben/abziehen

Team-Verwaltung:
• /teams - Übersicht aller Teams mit Mitgliedern

Nachrichten:
• /broadcast <text> - Nachricht an alle Spieler
• /message <id|name|@user> <text> - Nachricht an einen Spieler
• /teammessage <team_id> <text> - Nachricht an ein Team

Statistiken:
• /stats - Party-Statistiken (Spieler, Submissions, Top 3)
• /eastereggs (oder /films) - Alle erkannten Filme
• /apiusage - OpenAI API Nutzung und Kosten

System:
• /reset CONFIRM - Spiel zurücksetzen (ACHTUNG: Löscht alle Daten!)

Beispiele:
/player Fabian
/player @username
/player 657163418
/message Fabian Deine Punkte wurden korrigiert!
/broadcast Party beginnt in 30 Minuten! 🎉
/teammessage 417849 Großartige Leistung!
/points 657163418 50 Bonus für Kostüm
/stats
/teams
/apiusage

Hinweise:
• Alle Punkteänderungen werden im AdminLog protokolliert
• Spieler können per ID, Username oder Namen angesprochen werden
• Negative Punkte zum Abziehen verwenden
• Alle Commands funktionieren auch mit admin_ Präfix"""
    
    await update.message.reply_text(help_text)


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
    
    admin_menu = """🔧 ADMIN-MENÜ

Hilfe:
/help_admin - Ausführliche Hilfe mit Beispielen

Spieler-Verwaltung:
/players - Alle Spieler anzeigen
/player <ID|Name|@user> - Details zu einem Spieler
/points <user_id> <punkte> <grund> - Punkte vergeben/abziehen

Nachrichten:
/broadcast <text> - Nachricht an alle senden
/message <ID|Name|@user> <text> - Nachricht an einen Spieler
/teammessage <team_id> <text> - Nachricht an ein Team

Team & Stats:
/teams - Alle Teams anzeigen  
/stats - Party-Statistiken
/eastereggs (oder /films) - Erkannte Filme
/apiusage - OpenAI API Nutzung

System:
/reset CONFIRM - Spiel zurücksetzen (⚠️ VORSICHT!)

────────────────────────
Du bist eingeloggt als Admin.
💡 Tipp: Alle Commands funktionieren auch mit admin_ Präfix"""
    
    await update.message.reply_text(admin_menu)
    logger.info(f"Admin {user.id} accessed admin menu")


async def admin_players_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt alle Spieler mit ihren Punkten.
    
    Usage: /admin_players
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not config.is_admin(user.id):
        await context.bot.send_message(chat_id=chat_id, text="❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    db = Database()
    with db.get_session() as session:
        users = session.query(crud.User).order_by(crud.User.total_points.desc()).all()
        
        if not users:
            await context.bot.send_message(chat_id=chat_id, text="Noch keine Spieler registriert.")
            return
        
        message = "👥 ALLE SPIELER\n\n"
        
        for i, u in enumerate(users, 1):
            team_info = ""
            if u.team_id:
                team = session.query(crud.Team).filter_by(team_id=u.team_id).first()
                team_info = f" | Team: {team.film_title}" if team else ""
            
            message += f"{i}. {u.first_name} (@{u.username or 'N/A'})\n"
            message += f"   ID: {u.telegram_id} | Punkte: {u.total_points}{team_info}\n\n"
        
        await context.bot.send_message(chat_id=chat_id, text=message)
        logger.info(f"Admin {user.id} viewed all players")


async def admin_player_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt Details zu einem bestimmten Spieler.
    
    Usage: /player <telegram_id|username|name>
    Beispiele:
    - /player 657163418
    - /player @username
    - /player Fabian
    """
    user = update.effective_user
    
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    if not context.args or len(context.args) < 1:
        await update.message.reply_text(
            "❌ Ungültiges Format!\n\n"
            "Nutze: /player <telegram_id|username|name>\n\n"
            "Beispiele:\n"
            "• /player 657163418\n"
            "• /player @username\n"
            "• /player Fabian"
        )
        return
    
    # Alle Argumente zusammenfügen (für Namen mit Leerzeichen)
    identifier = " ".join(context.args)
    
    db = Database()
    with db.get_session() as session:
        player = crud.find_user_by_identifier(session, identifier)
        
        if not player:
            await update.message.reply_text(
                f"❌ Spieler '{identifier}' nicht gefunden.\n\n"
                f"Tipp: Verwende Telegram-ID, @username oder Namen."
            )
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
        
        message = f"""👤 SPIELER-DETAILS

Name: {player.first_name} {player.last_name or ''}
Username: @{player.username or 'N/A'}
Telegram-ID: {player.telegram_id}
DB-ID: {player.id}

📊 STATISTIKEN:
Gesamt-Punkte: {player.total_points}
Party-Fotos: {party_photos}
Film-Referenzen: {films}
Team: {team_info}

🎬 Erkannte Filme:
{films_list}

📅 Registriert: {player.created_at.strftime('%d.%m.%Y %H:%M')}"""
        
        await update.message.reply_text(message)
        logger.info(f"Admin {user.id} viewed player {identifier}")


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
        
        message = "🎬 ALLE TEAMS\n\n"
        
        for team in teams:
            members = session.query(crud.User).filter_by(team_id=team.team_id).all()
            member_count = len(members)
            
            message += f"{team.film_title} (ID: {team.team_id})\n"
            message += f"Charaktere: {team.character_1} & {team.character_2}\n"
            message += f"Mitglieder: {member_count}\n"
            
            if members:
                member_names = ", ".join([m.first_name for m in members])
                message += f"→ {member_names}\n"
            
            message += "\n"
        
        await update.message.reply_text(message)
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
        
        message = f"""📊 PARTY-STATISTIKEN

Gesamt:
👥 Spieler: {total_users}
📸 Submissions: {total_submissions}
⭐ Gesamt-Punkte: {sum_points}

Submissions nach Typ:
📷 Party-Fotos: {party_photos}
🎬 Film-Referenzen: {films}
👫 Team-Beitritte: {team_joins}
🧩 Puzzles gelöst: {puzzles}

Teams:
Aktive Teams: {teams_with_members}

🏆 TOP 3:"""
        
        for i, u in enumerate(top_users, 1):
            emoji = ["🥇", "🥈", "🥉"][i-1]
            message += f"\n{emoji} {u.first_name}: {u.total_points} Punkte"
        
        await update.message.reply_text(message)
        logger.info(f"Admin {user.id} viewed stats")


async def admin_points_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Vergibt/Entzieht Punkte manuell.
    
    Usage: /admin_points <telegram_id> <points> <reason>
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not config.is_admin(user.id):
        await context.bot.send_message(chat_id=chat_id, text="❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    if not context.args or len(context.args) < 3:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Ungültiges Format!\n\n"
            "Nutze: /points <telegram_id> <punkte> <grund>\n"
            "Beispiel: /points 123456789 10 Bonus für cooles Kostüm"
        )
        return
    
    telegram_id = int(context.args[0])
    points = int(context.args[1])
    reason = " ".join(context.args[2:])
    
    db = Database()
    with db.get_session() as session:
        player = session.query(crud.User).filter_by(telegram_id=telegram_id).first()
        
        if not player:
            await context.bot.send_message(chat_id=chat_id, text=f"❌ Spieler mit ID {telegram_id} nicht gefunden.")
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
        
        message = f"""✅ PUNKTE ANGEPASST

Spieler: {player.first_name}
Alte Punkte: {old_points}
Anpassung: {points:+d}
Neue Punkte: {player.total_points}

Grund: {reason}"""
        
        await context.bot.send_message(chat_id=chat_id, text=message)
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
        
        message = "🎬 ERKANNTE FILME\n\n"
        
        for film, users in sorted(films_dict.items()):
            message += f"{film} ({len(users)}x)\n"
            message += f"→ {', '.join(users)}\n\n"
        
        await update.message.reply_text(message)
        logger.info(f"Admin {user.id} viewed easter eggs")


async def admin_reset_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Setzt das Spiel zurück - VORSICHT: Löscht alle Daten!
    
    Usage: /reset CONFIRM
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not config.is_admin(user.id):
        await context.bot.send_message(chat_id=chat_id, text="❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    # Sicherheitsabfrage - User muss CONFIRM als Argument angeben
    if not context.args or len(context.args) != 1 or context.args[0] != 'CONFIRM':
        await context.bot.send_message(
            chat_id=chat_id,
            text="⚠️ GAME RESET\n\n"
            "Dieser Befehl löscht ALLE Spieldaten:\n"
            "• Alle Punkte werden auf 0 gesetzt\n"
            "• Alle Easter Eggs werden gelöscht\n"
            "• Alle Submissions werden gelöscht\n"
            "• Alle Team-Zuordnungen werden entfernt\n"
            "• User-Accounts bleiben erhalten\n"
            "• Team-Definitionen bleiben erhalten\n\n"
            "⚠️ DIESE AKTION KANN NICHT RÜCKGÄNGIG GEMACHT WERDEN!\n\n"
            "Um fortzufahren, nutze:\n"
            "/reset CONFIRM"
        )
        return
    
    db = Database()
    with db.get_session() as session:
        # Statistiken VOR dem Reset
        total_users = session.query(User).count()
        total_submissions = session.query(Submission).count()
        total_eggs = session.query(EasterEgg).count()
        total_points = sum([u.total_points for u in session.query(User).all()])
        users_with_teams = session.query(User).filter(User.team_id.isnot(None)).count()
        
        # 1. Alle Submissions löschen
        session.query(Submission).delete()
        
        # 2. Alle Easter Eggs löschen
        session.query(EasterEgg).delete()
        
        # 3. Alle User-Punkte auf 0 setzen UND Team-Zuordnung entfernen
        for user_obj in session.query(User).all():
            user_obj.total_points = 0
            user_obj.team_id = None  # Team-Zuordnung entfernen
        
        session.commit()
        
        message = f"""✅ GAME RESET ERFOLGREICH

🔄 Folgende Daten wurden zurückgesetzt:

👥 User: {total_users} (behalten)
📸 Submissions: {total_submissions} (gelöscht)
🎬 Easter Eggs: {total_eggs} (gelöscht)
⭐ Punkte: {total_points} → 0 (zurückgesetzt)
👫 Team-Zuordnungen: {users_with_teams} → 0 (entfernt)

Das Spiel wurde erfolgreich zurückgesetzt.
Alle Spieler können von vorne beginnen!"""
        
        await context.bot.send_message(chat_id=chat_id, text=message)
        logger.warning(f"Admin {user.id} has RESET THE GAME! Users: {total_users}, Submissions: {total_submissions}, Teams cleared: {users_with_teams}")


async def admin_apiusage_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Zeigt OpenAI API Nutzung und Token-Verbrauch.
    
    Usage: /apiusage
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    if not config.is_admin(user.id):
        await context.bot.send_message(chat_id=chat_id, text="❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    # Statistiken von ai_evaluator holen
    stats = ai_evaluator.get_usage_stats()
    
    # Geschätzte verbleibende Credits (OpenAI hat kein direktes API für Credits)
    # Das müsste manuell konfiguriert werden
    message = f"""📊 OPENAI API NUTZUNG

🤖 Requests:
• Total: {stats['total_requests']}
• Ø Tokens/Request: {stats['avg_tokens_per_request']}

🎯 Token-Verbrauch:
• Total Tokens: {stats['total_tokens_used']:,}

💰 Kosten (geschätzt):
• Total: ${stats['total_cost_usd']:.4f} USD

📝 Hinweis:
• GPT-4o Kosten: ~$0.005/1K input, ~$0.015/1K output tokens
• Diese Statistiken gelten seit letztem Bot-Neustart
• Für genaue Credits: OpenAI Dashboard prüfen

🔗 OpenAI Dashboard:
https://platform.openai.com/usage"""
    
    await context.bot.send_message(chat_id=chat_id, text=message)
    logger.info(f"Admin {user.id} viewed API usage stats")


async def admin_broadcast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sendet eine Nachricht an alle Spieler.
    
    Usage: /broadcast <nachricht>
    Beispiel: /broadcast Party beginnt in 30 Minuten! 🎉
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob User Admin ist
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    # Nachricht extrahieren
    if not context.args:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Verwendung: /broadcast <nachricht>\n\n"
                 "Beispiel: /broadcast Party beginnt in 30 Minuten! 🎉"
        )
        return
    
    message = " ".join(context.args)
    
    # Alle Benutzer aus der Datenbank holen
    db = Database()
    
    with db.get_session() as session:
        users = crud.get_all_users(session)
        
        if not users:
            await context.bot.send_message(chat_id=chat_id, text="❌ Keine Benutzer gefunden.")
            return
        
        # Nachricht an alle senden
        success_count = 0
        fail_count = 0
        
        broadcast_message = f"📢 ADMIN-NACHRICHT:\n\n{message}"
        
        for target_user in users:
            try:
                await context.bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=broadcast_message
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send broadcast to user {target_user.telegram_id}: {e}")
                fail_count += 1
        
        # Bestätigung an Admin
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Broadcast gesendet!\n\n"
                 f"📤 Erfolgreich: {success_count}\n"
                 f"❌ Fehlgeschlagen: {fail_count}\n\n"
                 f"Nachricht:\n{message}"
        )
        logger.info(f"Admin {user.id} sent broadcast to {success_count} users (failed: {fail_count})")


async def admin_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sendet eine Nachricht an einen einzelnen Spieler.
    
    Usage: /message <user_id_or_name> <nachricht>
    Beispiel: /message 657163418 Bitte melde dich!
    Beispiel: /message @username Deine Punkte wurden korrigiert
    Beispiel: /message Fabian Gut gemacht!
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob User Admin ist
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    # Mindestens 2 Argumente erforderlich
    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Verwendung: /message <user_id_or_name> <nachricht>\n\n"
                 "Beispiele:\n"
                 "• /message 657163418 Hallo!\n"
                 "• /message @username Deine Punkte wurden aktualisiert\n"
                 "• /message Fabian Gut gemacht!"
        )
        return
    
    user_identifier = context.args[0]
    message = " ".join(context.args[1:])
    
    # Benutzer finden (per ID, Username oder Name)
    db = Database()
    
    with db.get_session() as session:
        target_user = crud.find_user_by_identifier(session, user_identifier)
        
        if not target_user:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Benutzer '{user_identifier}' nicht gefunden.\n\n"
                     f"Tipp: Verwende Telegram-ID, @username oder Namen."
            )
            return
        
        # Nachricht senden
        admin_message = f"📨 NACHRICHT VOM ADMIN:\n\n{message}"
        
        try:
            await context.bot.send_message(
                chat_id=target_user.telegram_id,
                text=admin_message
            )
            
            # Bestätigung an Admin
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"✅ Nachricht gesendet an:\n"
                     f"👤 {target_user.first_name or 'N/A'} "
                     f"(@{target_user.username or 'N/A'}) "
                     f"[ID: {target_user.telegram_id}]\n\n"
                     f"Nachricht:\n{message}"
            )
            logger.info(f"Admin {user.id} sent message to user {target_user.telegram_id}")
            
        except Exception as e:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Fehler beim Senden der Nachricht: {str(e)}"
            )
            logger.error(f"Failed to send message to user {target_user.telegram_id}: {e}")


async def admin_team_message_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Sendet eine Nachricht an alle Mitglieder eines Teams.
    
    Usage: /teammessage <team_id> <nachricht>
    Beispiel: /teammessage 417849 Euer Team liegt auf Platz 1! 🏆
    """
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Prüfen ob User Admin ist
    if not config.is_admin(user.id):
        await update.message.reply_text("❌ Dieser Command ist nur für Admins verfügbar.")
        return
    
    # Mindestens 2 Argumente erforderlich
    if len(context.args) < 2:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Verwendung: /teammessage <team_id> <nachricht>\n\n"
                 "Beispiel: /teammessage 417849 Großartige Leistung! 🎉"
        )
        return
    
    try:
        team_id = int(context.args[0])
    except ValueError:
        await context.bot.send_message(
            chat_id=chat_id,
            text="❌ Team-ID muss eine Zahl sein.\n\n"
                 "Beispiel: /teammessage 417849 Nachricht"
        )
        return
    
    message = " ".join(context.args[1:])
    
    # Team-Mitglieder finden
    db = Database()
    
    with db.get_session() as session:
        team = crud.get_team_by_id(session, team_id)
        
        if not team:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Team {team_id} nicht gefunden."
            )
            return
        
        # Alle Mitglieder des Teams holen
        team_users = crud.get_users_by_team(session, team_id)
        
        if not team_users:
            await context.bot.send_message(
                chat_id=chat_id,
                text=f"❌ Team {team_id} ({team.film_title}) hat keine Mitglieder."
            )
            return
        
        # Nachricht an alle Team-Mitglieder senden
        success_count = 0
        fail_count = 0
        
        team_message = f"📢 TEAM-NACHRICHT ({team.film_title}):\n\n{message}"
        
        for target_user in team_users:
            try:
                await context.bot.send_message(
                    chat_id=target_user.telegram_id,
                    text=team_message
                )
                success_count += 1
            except Exception as e:
                logger.warning(f"Failed to send team message to user {target_user.telegram_id}: {e}")
                fail_count += 1
        
        # Bestätigung an Admin
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"✅ Team-Nachricht gesendet!\n\n"
                 f"🎬 Team: {team.film_title} (ID: {team_id})\n"
                 f"📤 Erfolgreich: {success_count}\n"
                 f"❌ Fehlgeschlagen: {fail_count}\n\n"
                 f"Nachricht:\n{message}"
        )
        logger.info(f"Admin {user.id} sent team message to team {team_id} ({success_count} users)")

