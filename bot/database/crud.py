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
    session.commit()
    
    # Punkte zum User hinzufügen
    if points_awarded > 0:
        update_user_points(session, user_id, points_awarded)
    
    logger.info(f"Submission created: {submission.id} (type={submission_type.value}, points={points_awarded})")
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
    
    # Zähle Submissions nach Typ
    party_count = count_user_submissions(session, user_id, SubmissionType.PARTY_PHOTO)
    film_count = count_user_submissions(session, user_id, SubmissionType.FILM_REFERENCE)
    
    # Puzzle und Team
    has_team = user.team_id is not None
    solved_puzzle = has_solved_puzzle(session, user_id)
    
    # Erkannte Filme
    recognized_films = get_user_easter_eggs(session, user_id)
    
    # Ranking
    ranking, total_users = get_user_ranking(session, user_id)
    
    return {
        'total_points': user.total_points,
        'party_photos_count': party_count,
        'party_points': party_count * 1,
        'film_count': film_count,
        'film_points': film_count * 20,
        'team_points': 25 if has_team else 0,
        'puzzle_points': 25 if solved_puzzle else 0,
        'team_name': user.team.film_title if user.team else None,
        'recognized_films': recognized_films,
        'ranking': ranking,
        'total_users': total_users
    }
