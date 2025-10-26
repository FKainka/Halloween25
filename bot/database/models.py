"""
SQLAlchemy Datenbank-Modelle für den Halloween Bot.
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, String, BigInteger, Boolean, 
    DateTime, Text, ForeignKey, Enum as SQLEnum
)
from sqlalchemy.orm import declarative_base, relationship
import enum

Base = declarative_base()


class SubmissionType(enum.Enum):
    """Typ der Foto-Submission."""
    PARTY_PHOTO = "party_photo"
    FILM_REFERENCE = "film_reference"
    TEAM_JOIN = "team_join"
    PUZZLE = "puzzle"


class SubmissionStatus(enum.Enum):
    """Status der Submission."""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class User(Base):
    """User-Modell für Spieler."""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255), nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    team_id = Column(String(6), ForeignKey('teams.team_id'), nullable=True)
    total_points = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    is_admin = Column(Boolean, default=False, nullable=False)
    
    # Relationships
    team = relationship("Team", back_populates="members")
    submissions = relationship("Submission", back_populates="user")
    easter_eggs = relationship("EasterEgg", back_populates="user")
    
    def __repr__(self):
        return f"<User(telegram_id={self.telegram_id}, name={self.first_name}, points={self.total_points})>"


class Team(Base):
    """Team-Modell basierend auf Film-Charakteren."""
    __tablename__ = "teams"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    team_id = Column(String(6), unique=True, nullable=False, index=True)
    film_title = Column(String(255), nullable=False)
    character_1 = Column(String(255), nullable=False)
    character_2 = Column(String(255), nullable=False)
    character_1_id = Column(String(6), nullable=False)
    character_2_id = Column(String(6), nullable=False)
    puzzle_link = Column(String(500), nullable=True)  # Optional für Admin-Team
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    members = relationship("User", back_populates="team")
    
    def __repr__(self):
        return f"<Team(team_id={self.team_id}, film={self.film_title}, members={len(self.members)})>"


class Submission(Base):
    """Foto-Submissions von Usern."""
    __tablename__ = "submissions"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    submission_type = Column(SQLEnum(SubmissionType), nullable=False)
    photo_file_id = Column(String(500), nullable=True)  # Telegram File-ID
    photo_path = Column(String(500), nullable=True)  # Lokaler Pfad
    thumbnail_path = Column(String(500), nullable=True)  # Thumbnail Pfad
    caption = Column(Text, nullable=True)
    film_title = Column(String(255), nullable=True)  # Bei Film-Referenz
    points_awarded = Column(Integer, default=0, nullable=False)
    ai_evaluation = Column(Text, nullable=True)  # JSON mit KI-Bewertung
    status = Column(SQLEnum(SubmissionStatus), default=SubmissionStatus.PENDING, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="submissions")
    
    def __repr__(self):
        return f"<Submission(id={self.id}, type={self.submission_type.value}, status={self.status.value})>"


class EasterEgg(Base):
    """Erkannte Film-Referenzen (Easter Eggs)."""
    __tablename__ = "easter_eggs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    film_title = Column(String(255), nullable=False)
    recognized_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # Relationships
    user = relationship("User", back_populates="easter_eggs")
    
    def __repr__(self):
        return f"<EasterEgg(user_id={self.user_id}, film={self.film_title})>"


class AdminLog(Base):
    """Logs für Admin-Aktionen."""
    __tablename__ = "admin_logs"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    admin_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    action = Column(String(255), nullable=False)
    target_user_id = Column(Integer, nullable=True)
    details = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    def __repr__(self):
        return f"<AdminLog(admin_id={self.admin_id}, action={self.action})>"
