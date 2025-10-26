"""
Datenbank-Setup und Session-Management.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from contextlib import contextmanager
import logging

from database.models import Base
from config import config

logger = logging.getLogger('bot.database')


class Database:
    """Datenbank-Verwaltung."""
    
    def __init__(self, database_url: str = None):
        """
        Initialisiert die Datenbank-Verbindung.
        
        Args:
            database_url: URL zur Datenbank (default: aus config)
        """
        self.database_url = database_url or config.DATABASE_URL
        
        # Engine erstellen
        self.engine = create_engine(
            self.database_url,
            echo=False,  # SQL-Queries nicht loggen (zu verbose)
            pool_pre_ping=True  # Connection-Check vor Verwendung
        )
        
        # Session Factory
        self.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )
        
        logger.info(f"Database initialized: {self.database_url}")
    
    def create_tables(self):
        """Erstellt alle Tabellen in der Datenbank."""
        logger.info("Creating database tables...")
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def drop_tables(self):
        """Löscht alle Tabellen (nur für Development!)."""
        logger.warning("Dropping all database tables...")
        Base.metadata.drop_all(bind=self.engine)
        logger.warning("All tables dropped")
    
    @contextmanager
    def get_session(self) -> Session:
        """
        Context Manager für Datenbank-Sessions.
        
        Usage:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Database session error: {e}", exc_info=True)
            raise
        finally:
            session.close()


# Globale Datenbank-Instanz
db = Database()
