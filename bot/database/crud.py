"""
CRUD-Operationen für die Datenbank.
"""

from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional, List
import logging

from database.models import (
    User, Team, Submission, EasterEgg, AdminLog,
    SubmissionType, SubmissionStatus
)

logger = logging.getLogger('bot.database.crud')


# ============================================================================
# USER OPERATIONS
# ============================================================================

def get_or_create_user(
    session: Session,
    telegram_id: int,
    username: str = None,
    first_name: str = None,
    last_name: str = None
) -> User:
    """
    Holt User aus DB oder erstellt neuen User.
    
    Args:
        session: DB-Session
        telegram_id: Telegram User-ID
        username: Telegram Username
        first_name: Vorname
        last_name: Nachname
    
    Returns:
        User: User-Objekt
    """
    user = session.query(User).filter(User.telegram_id == telegram_id).first()
    
    if not user:
        user = User(
            telegram_id=telegram_id,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        session.add(user)
        session.commit()
        logger.info(f"New user created: {telegram_id} ({first_name})")
    
    return user


def get_user_by_telegram_id(session: Session, telegram_id: int) -> Optional[User]:
    """Holt User anhand Telegram-ID."""
    return session.query(User).filter(User.telegram_id == telegram_id).first()


def update_user_points(session: Session, user_id: int, points: int):
    """Aktualisiert User-Punkte."""
    user = session.query(User).filter(User.id == user_id).first()
    if user:
        user.total_points += points
        session.commit()
        logger.info(f"User {user_id} points updated: +{points} (total: {user.total_points})")


def get_user_ranking(session: Session, user_id: int) -> tuple[int, int]:
    """
    Gibt Ranking des Users zurück.
    
    Returns:
        tuple: (ranking_position, total_users)
    """
    user = session.query(User).filter(User.id == user_id).first()
    if not user:
        return (0, 0)
    
    # Zähle User mit mehr Punkten
    higher_ranked = session.query(User).filter(User.total_points > user.total_points).count()
    total_users = session.query(User).count()
    
    return (higher_ranked + 1, total_users)


def get_all_users(session: Session) -> List[User]:
    """Holt alle User aus der Datenbank."""
    return session.query(User).all()


def get_users_by_team(session: Session, team_id: str) -> List[User]:
    """Holt alle User eines Teams."""
    return session.query(User).filter(User.team_id == team_id).all()


def find_user_by_identifier(session: Session, identifier: str) -> Optional[User]:
    """
    Findet einen User anhand verschiedener Identifikatoren:
    - Telegram-ID (numerisch)
    - Username (mit oder ohne @)
    - Vorname
    - Nachname
    - Vollständiger Name (Vorname + Nachname)
    
    Args:
        session: DB-Session
        identifier: Suchstring (ID, Username oder Name)
    
    Returns:
        User oder None
    """
    # Versuche als Telegram-ID
    try:
        telegram_id = int(identifier)
        user = session.query(User).filter(User.telegram_id == telegram_id).first()
        if user:
            return user
    except ValueError:
        pass
    
    # Entferne @ falls vorhanden
    clean_identifier = identifier.lstrip('@').lower()
    
    # Suche nach Username
    user = session.query(User).filter(
        func.lower(User.username) == clean_identifier
    ).first()
    if user:
        return user
    
    # Suche nach Vorname
    user = session.query(User).filter(
        func.lower(User.first_name) == clean_identifier
    ).first()
    if user:
        return user
    
    # Suche nach Nachname
    user = session.query(User).filter(
        func.lower(User.last_name) == clean_identifier
    ).first()
    if user:
        return user
    
    # Suche nach vollständigem Namen (Vorname + Nachname)
    users = session.query(User).all()
    for user in users:
        full_name = f"{user.first_name or ''} {user.last_name or ''}".strip().lower()
        if full_name == clean_identifier:
            return user
    
    return None


# ============================================================================
# TEAM OPERATIONS
# ============================================================================

def create_team(
    session: Session,
    team_id: str,
    film_title: str,
    character_1: str,
    character_2: str,
    character_1_id: str,
    character_2_id: str,
    puzzle_link: str
) -> Team:
    """Erstellt ein neues Team."""
    team = Team(
        team_id=team_id,
        film_title=film_title,
        character_1=character_1,
        character_2=character_2,
        character_1_id=character_1_id,
        character_2_id=character_2_id,
        puzzle_link=puzzle_link
    )
    session.add(team)
    session.commit()
    logger.info(f"Team created: {team_id} ({film_title})")
    return team


def get_team_by_id(session: Session, team_id: str) -> Optional[Team]:
    """Holt Team anhand Team-ID."""
    return session.query(Team).filter(Team.team_id == team_id).first()


def join_team(session: Session, user_id: int, team_id: str) -> bool:
    """
    User tritt Team bei.
    
    Returns:
        bool: True wenn erfolgreich, False wenn bereits in Team
    """
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        return False
    
    if user.team_id:
        logger.warning(f"User {user_id} already in team {user.team_id}")
        return False
    
    user.team_id = team_id
    session.commit()
    logger.info(f"User {user_id} joined team {team_id}")
    return True


# ============================================================================
# SUBMISSION OPERATIONS
# ============================================================================

def create_submission(
    session: Session,
    user_id: int,
    submission_type: SubmissionType,
    photo_file_id: str = None,
    photo_path: str = None,
    thumbnail_path: str = None,
    caption: str = None,
    film_title: str = None,
    points_awarded: int = 0,
    status: SubmissionStatus = SubmissionStatus.APPROVED
) -> Submission:
    """Erstellt eine neue Submission."""
    submission = Submission(
        user_id=user_id,
        submission_type=submission_type,
        photo_file_id=photo_file_id,
        photo_path=photo_path,
        thumbnail_path=thumbnail_path,
        caption=caption,
        film_title=film_title,
        points_awarded=points_awarded,
        status=status
    )
    session.add(submission)
    session.flush()  # Flush um ID zu bekommen, aber noch nicht committen
    
    # Punkte zum User hinzufügen (nur wenn status APPROVED ist)
    if points_awarded > 0 and status == SubmissionStatus.APPROVED:
        update_user_points(session, user_id, points_awarded)
    
    session.commit()
    
    logger.info(f"Submission created: {submission.id} (type={submission_type.value}, points={points_awarded}, status={status.value})")
    return submission


def get_user_submissions(
    session: Session,
    user_id: int,
    submission_type: SubmissionType = None
) -> List[Submission]:
    """Holt alle Submissions eines Users."""
    query = session.query(Submission).filter(Submission.user_id == user_id)
    
    if submission_type:
        query = query.filter(Submission.submission_type == submission_type)
    
    return query.all()


def count_user_submissions(
    session: Session,
    user_id: int,
    submission_type: SubmissionType
) -> int:
    """Zählt Submissions eines Users nach Typ."""
    return session.query(Submission).filter(
        Submission.user_id == user_id,
        Submission.submission_type == submission_type
    ).count()


def update_submission_status(
    session: Session,
    submission_id: int,
    status: SubmissionStatus,
    points_awarded: int = None,
    ai_evaluation: str = None
):
    """
    Aktualisiert den Status einer Submission und vergibt Punkte.
    
    Args:
        session: DB-Session
        submission_id: ID der Submission
        status: Neuer Status
        points_awarded: Zu vergebende Punkte (optional)
        ai_evaluation: AI Evaluation JSON (optional)
    """
    submission = session.query(Submission).filter(Submission.id == submission_id).first()
    
    if not submission:
        logger.error(f"Submission {submission_id} not found")
        return
    
    old_status = submission.status
    submission.status = status
    
    if ai_evaluation is not None:
        submission.ai_evaluation = ai_evaluation
    
    # Punkte vergeben wenn APPROVED und Punkte gesetzt
    if status == SubmissionStatus.APPROVED and points_awarded is not None:
        old_points = submission.points_awarded
        submission.points_awarded = points_awarded
        
        # Nur Differenz zu den bereits vergebenen Punkten hinzufügen
        points_diff = points_awarded - old_points
        if points_diff > 0:
            update_user_points(session, submission.user_id, points_diff)
            logger.info(f"Submission {submission_id}: Added {points_diff} points (was {old_points}, now {points_awarded})")
    
    session.commit()
    logger.info(f"Submission {submission_id} status updated: {old_status.value} -> {status.value}")


def has_solved_puzzle(session: Session, user_id: int) -> bool:
    """Prüft ob User Puzzle gelöst hat."""
    return session.query(Submission).filter(
        Submission.user_id == user_id,
        Submission.submission_type == SubmissionType.PUZZLE,
        Submission.status == SubmissionStatus.APPROVED
    ).count() > 0


# ============================================================================
# EASTER EGG OPERATIONS
# ============================================================================

def has_recognized_film(session: Session, user_id: int, film_title: str) -> bool:
    """Prüft ob User einen Film bereits erkannt hat."""
    return session.query(EasterEgg).filter(
        EasterEgg.user_id == user_id,
        EasterEgg.film_title == film_title
    ).count() > 0


def add_easter_egg(session: Session, user_id: int, film_title: str) -> EasterEgg:
    """Fügt erkannten Film hinzu."""
    easter_egg = EasterEgg(
        user_id=user_id,
        film_title=film_title
    )
    session.add(easter_egg)
    session.commit()
    logger.info(f"Easter egg added: User {user_id} recognized {film_title}")
    return easter_egg


def get_user_easter_eggs(session: Session, user_id: int) -> List[str]:
    """Holt alle erkannten Filme eines Users."""
    eggs = session.query(EasterEgg).filter(EasterEgg.user_id == user_id).all()
    return [egg.film_title for egg in eggs]


def get_top_players(session: Session, limit: int = 3) -> List[dict]:
    """
    Holt die Top-Spieler nach Punkten.
    
    Args:
        session: DB-Session
        limit: Anzahl der Spieler
    
    Returns:
        List[dict]: Liste mit {name, points, team}
    """
    users = session.query(User).order_by(User.total_points.desc()).limit(limit).all()
    
    result = []
    for user in users:
        result.append({
            'name': user.first_name or user.username or f"User {user.telegram_id}",
            'points': user.total_points,
            'team': user.team.film_title if user.team else None
        })
    
    return result


def get_top_teams(session: Session, limit: int = 3) -> List[dict]:
    """
    Holt die Top-Teams nach Gesamtpunkten der Mitglieder.
    
    Args:
        session: DB-Session
        limit: Anzahl der Teams
    
    Returns:
        List[dict]: Liste mit {team_name, total_points, member_count}
    """
    # Gruppiere User nach Team und summiere Punkte
    results = session.query(
        User.team_id,
        func.sum(User.total_points).label('total_points'),
        func.count(User.id).label('member_count')
    ).filter(
        User.team_id.isnot(None)
    ).group_by(
        User.team_id
    ).order_by(
        func.sum(User.total_points).desc()
    ).limit(limit).all()
    
    team_list = []
    for team_id, total_points, member_count in results:
        team = get_team_by_id(session, team_id)
        if team:
            team_list.append({
                'team_name': team.film_title,
                'total_points': int(total_points) if total_points else 0,
                'member_count': member_count
            })
    
    return team_list


# ============================================================================
# STATISTICS
# ============================================================================

def get_user_stats(session: Session, user_id: int) -> dict:
    """
    Holt detaillierte Statistiken für einen User.
    
    Returns:
        dict: Statistiken mit Punkten, Submissions, etc.
    """
    user = session.query(User).filter(User.id == user_id).first()
    
    if not user:
        return {}
    
    # Zähle Party Photos (alle zählen als approved)
    party_count = count_user_submissions(session, user_id, SubmissionType.PARTY_PHOTO)
    
    # Film-Referenzen: Eingereicht vs. Korrekt
    film_submitted = session.query(Submission).filter(
        Submission.user_id == user_id,
        Submission.submission_type == SubmissionType.FILM_REFERENCE
    ).count()
    
    film_approved = session.query(Submission).filter(
        Submission.user_id == user_id,
        Submission.submission_type == SubmissionType.FILM_REFERENCE,
        Submission.status == SubmissionStatus.APPROVED
    ).count()
    
    # Puzzle und Team
    has_team = user.team_id is not None
    solved_puzzle = has_solved_puzzle(session, user_id)
    
    # Erkannte Filme (nur genehmigte)
    recognized_films = get_user_easter_eggs(session, user_id)
    
    # Ranking
    ranking, total_users = get_user_ranking(session, user_id)
    
    return {
        'total_points': user.total_points,
        'party_photos_count': party_count,
        'party_points': party_count * 1,
        'film_submitted': film_submitted,
        'film_approved': film_approved,
        'film_count': film_approved,  # Backward compatibility
        'film_points': film_approved * 20,
        'team_points': 25 if has_team else 0,
        'puzzle_points': 25 if solved_puzzle else 0,
        'team_name': user.team.film_title if user.team else None,
        'recognized_films': recognized_films,
        'ranking': ranking,
        'total_users': total_users
    }
