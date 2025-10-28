"""
Datenbank-Setup und Session-Management.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import contextmanager
import logging
import time
from functools import wraps

from database.models import Base
from config import config

logger = logging.getLogger('bot.database')


def retry_on_db_lock(max_retries=3, delay=0.5):
    """
    Decorator für automatische Retries bei Database Lock Errors.
    
    Args:
        max_retries: Maximale Anzahl an Versuchen
        delay: Wartezeit zwischen Versuchen in Sekunden
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_msg = str(e).lower()
                    if 'database is locked' in error_msg or 'locked' in error_msg:
                        if attempt < max_retries - 1:
                            wait_time = delay * (2 ** attempt)  # Exponential backoff
                            logger.warning(f"Database locked, retry {attempt + 1}/{max_retries} in {wait_time}s")
                            time.sleep(wait_time)
                            continue
                    raise
            return None
        return wrapper
    return decorator


class Database:
    """Datenbank-Verwaltung."""
    
    def __init__(self, database_url: str = None):
        """
        Initialisiert die Datenbank-Verbindung.
        
        Args:
            database_url: URL zur Datenbank (default: aus config)
        """
        self.database_url = database_url or config.DATABASE_URL
        
        # Prüfen ob SQLite
        is_sqlite = self.database_url.startswith('sqlite')
        
        # Engine-Konfiguration
        engine_kwargs = {
            'echo': False,  # SQL-Queries nicht loggen (zu verbose)
            'pool_pre_ping': True  # Connection-Check vor Verwendung
        }
        
        # SQLite-spezifische Optimierungen
        if is_sqlite:
            engine_kwargs.update({
                'connect_args': {
                    'check_same_thread': False,  # Threading erlauben
                    'timeout': 30.0,  # 30 Sekunden Timeout statt 5
                    'isolation_level': None  # Autocommit mode für bessere Concurrency
                },
                'poolclass': StaticPool,  # StaticPool für SQLite
            })
            logger.info("Using SQLite with optimized settings for concurrency")
        
        # Engine erstellen
        self.engine = create_engine(self.database_url, **engine_kwargs)
        
        # SQLite Pragma setzen für bessere Concurrency
        if is_sqlite:
            @event.listens_for(self.engine, "connect")
            def set_sqlite_pragma(dbapi_conn, connection_record):
                cursor = dbapi_conn.cursor()
                cursor.execute("PRAGMA journal_mode=WAL")  # Write-Ahead Logging
                cursor.execute("PRAGMA busy_timeout=30000")  # 30 Sekunden busy timeout
                cursor.execute("PRAGMA synchronous=NORMAL")  # Balance zwischen Safety und Speed
                cursor.close()
            logger.info("SQLite WAL mode enabled for better concurrency")
        
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
        Context Manager für Datenbank-Sessions mit automatischem Retry.
        
        Usage:
            with db.get_session() as session:
                user = session.query(User).first()
        """
        max_retries = 3
        retry_delay = 0.5
        
        for attempt in range(max_retries):
            session = self.SessionLocal()
            try:
                yield session
                session.commit()
                break  # Erfolg, kein Retry nötig
            except Exception as e:
                session.rollback()
                error_msg = str(e).lower()
                
                # Prüfen ob Database Lock Error
                if ('database is locked' in error_msg or 'locked' in error_msg) and attempt < max_retries - 1:
                    wait_time = retry_delay * (2 ** attempt)  # Exponential backoff
                    logger.warning(
                        f"Database locked on attempt {attempt + 1}/{max_retries}, "
                        f"retrying in {wait_time}s... Error: {e}"
                    )
                    session.close()
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"Database session error: {e}", exc_info=True)
                    raise
            finally:
                if session.is_active:
                    session.close()


# Globale Datenbank-Instanz
db = Database()
