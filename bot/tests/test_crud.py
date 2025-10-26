"""
Unit Tests für database/crud.py
"""
import pytest
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from database.models import Base, User, Team, Submission, EasterEgg, SubmissionType, SubmissionStatus
from database import crud


@pytest.fixture
def test_db():
    """Erstellt eine temporäre In-Memory SQLite Datenbank für Tests"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Test-Teams hinzufügen
    team1 = Team(
        team_id=480514,
        film_title="Matrix",
        character_1="Trinity",
        character_2="Neo",
        character_1_id=246935,
        character_2_id=233579,
        puzzle_link="https://www.jigsawplanet.com/?rc=play&pid=matrix"
    )
    team2 = Team(
        team_id=500000,
        film_title="Terminator",
        character_1="Sarah Connor",
        character_2="John Connor",
        character_1_id=250000,
        character_2_id=250000,
        puzzle_link="https://www.jigsawplanet.com/?rc=play&pid=terminator"
    )
    session.add_all([team1, team2])
    session.commit()
    
    yield session
    
    session.close()


class TestUserOperations:
    """Tests für User-bezogene CRUD Operationen"""
    
    def test_get_or_create_user_new(self, test_db):
        """Test: Neuen User erstellen"""
        user = crud.get_or_create_user(
            test_db,
            telegram_id=123456789,
            username="testuser",
            first_name="Test",
            last_name="User"
        )
        
        assert user is not None
        assert user.telegram_id == 123456789
        assert user.username == "testuser"
        assert user.first_name == "Test"
        assert user.last_name == "User"
        assert user.total_points == 0
        assert user.is_admin is False
    
    def test_get_or_create_user_existing(self, test_db):
        """Test: Existierenden User abrufen"""
        # Ersten User erstellen
        user1 = crud.get_or_create_user(
            test_db,
            telegram_id=123456789,
            username="testuser"
        )
        
        # Gleichen User nochmal abrufen
        user2 = crud.get_or_create_user(
            test_db,
            telegram_id=123456789,
            username="testuser_updated"
        )
        
        assert user1.id == user2.id
        assert user1.telegram_id == user2.telegram_id
    
    def test_get_user_stats_empty(self, test_db):
        """Test: Statistiken für User ohne Submissions"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        stats = crud.get_user_stats(test_db, user.telegram_id)
        
        assert stats["total_points"] == 0
        assert stats["party_photos_count"] == 0
        assert stats["film_count"] == 0
        assert stats["team_points"] == 0
        assert stats["puzzle_points"] == 0
        assert stats["recognized_films"] == []
        assert stats["ranking"] == 1
        assert stats["total_users"] == 1
    
    def test_get_user_stats_with_data(self, test_db):
        """Test: Statistiken für User mit verschiedenen Submissions"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        # Party Foto
        crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.PARTY_PHOTO,
            photo_file_id="file1",
            photo_path="/path/to/photo1.jpg",
            points_awarded=1
        )
        
        # Film Recognition
        crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.FILM_REFERENCE,
            photo_file_id="file2",
            photo_path="/path/to/photo2.jpg",
            caption="Film: Matrix",
            film_title="Matrix",
            points_awarded=20,
            status=SubmissionStatus.APPROVED
        )
        
        # Team Join
        crud.join_team(test_db, user.telegram_id, 480514)
        crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.TEAM_JOIN,
            points_awarded=25
        )
        
        stats = crud.get_user_stats(test_db, user.telegram_id)
        
        assert stats["total_points"] == 46  # 1 + 20 + 25
        assert stats["party_photos_count"] == 1
        assert stats["film_count"] == 1
        assert stats["team_points"] == 25
        assert stats["puzzle_points"] == 0
        assert stats["team_name"] == "Matrix"


class TestTeamOperations:
    """Tests für Team-bezogene CRUD Operationen"""
    
    def test_join_team_success(self, test_db):
        """Test: User tritt Team bei"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        result = crud.join_team(test_db, user.telegram_id, 480514)
        
        assert result is True
        
        # User neu laden und Team prüfen
        test_db.refresh(user)
        assert user.team_id == 480514
    
    def test_join_team_invalid_id(self, test_db):
        """Test: User versucht ungültiges Team beizutreten"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        result = crud.join_team(test_db, user.telegram_id, 999999)
        
        assert result is False
        assert user.team_id is None
    
    def test_join_team_already_member(self, test_db):
        """Test: User ist bereits in einem Team"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        # Erstes Team beitreten
        crud.join_team(test_db, user.telegram_id, 480514)
        test_db.refresh(user)
        assert user.team_id == 480514
        
        # Versuch, zweites Team beizutreten
        result = crud.join_team(test_db, user.telegram_id, 500000)
        test_db.refresh(user)
        
        # Team sollte NICHT gewechselt werden
        assert user.team_id == 480514


class TestSubmissionOperations:
    """Tests für Submission-bezogene CRUD Operationen"""
    
    def test_create_submission_party_photo(self, test_db):
        """Test: Party Photo Submission erstellen"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        submission = crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.PARTY_PHOTO,
            photo_file_id="file123",
            photo_path="/photos/party/123_photo.jpg",
            thumbnail_path="/photos/party/123_thumb.jpg",
            points_awarded=1
        )
        
        assert submission is not None
        assert submission.user_id == user.id
        assert submission.submission_type == SubmissionType.PARTY_PHOTO
        assert submission.points_awarded == 1
        assert submission.status == SubmissionStatus.APPROVED
        
        # User-Punkte prüfen
        test_db.refresh(user)
        assert user.total_points == 1
    
    def test_create_submission_film_reference(self, test_db):
        """Test: Film Reference Submission erstellen"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        submission = crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.FILM_REFERENCE,
            photo_file_id="file456",
            photo_path="/photos/films/matrix.jpg",
            caption="Film: Matrix",
            film_title="Matrix",
            points_awarded=20,
            status=SubmissionStatus.APPROVED
        )
        
        assert submission.film_title == "Matrix"
        assert submission.points_awarded == 20
        
        test_db.refresh(user)
        assert user.total_points == 20
    
    def test_has_recognized_film_true(self, test_db):
        """Test: User hat Film bereits erkannt"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        # Ersten Film erkennen
        crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.FILM_REFERENCE,
            photo_file_id="file1",
            photo_path="/path/to/photo.jpg",
            film_title="Matrix",
            points_awarded=20,
            status=SubmissionStatus.APPROVED
        )
        
        # Easter Egg erstellen
        easter_egg = EasterEgg(
            user_id=user.id,
            film_title="Matrix"
        )
        test_db.add(easter_egg)
        test_db.commit()
        
        # Prüfen
        result = crud.has_recognized_film(test_db, user.telegram_id, "Matrix")
        assert result is True
    
    def test_has_recognized_film_false(self, test_db):
        """Test: User hat Film noch nicht erkannt"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        
        result = crud.has_recognized_film(test_db, user.telegram_id, "Matrix")
        assert result is False
    
    def test_has_solved_puzzle_true(self, test_db):
        """Test: User hat Puzzle bereits gelöst"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        crud.join_team(test_db, user.telegram_id, 480514)
        
        # Puzzle Submission erstellen
        crud.create_submission(
            test_db,
            user_id=user.id,
            submission_type=SubmissionType.PUZZLE,
            photo_file_id="puzzle1",
            photo_path="/photos/puzzles/puzzle.jpg",
            points_awarded=25,
            status=SubmissionStatus.APPROVED
        )
        
        result = crud.has_solved_puzzle(test_db, user.telegram_id, 480514)
        assert result is True
    
    def test_has_solved_puzzle_false(self, test_db):
        """Test: User hat Puzzle noch nicht gelöst"""
        user = crud.get_or_create_user(test_db, telegram_id=123456789)
        crud.join_team(test_db, user.telegram_id, 480514)
        
        result = crud.has_solved_puzzle(test_db, user.telegram_id, 480514)
        assert result is False


class TestRanking:
    """Tests für Ranking-System"""
    
    def test_ranking_multiple_users(self, test_db):
        """Test: Ranking mit mehreren Usern"""
        # User 1: 50 Punkte
        user1 = crud.get_or_create_user(test_db, telegram_id=111111111)
        crud.create_submission(test_db, user_id=user1.id, submission_type=SubmissionType.PARTY_PHOTO, 
                             photo_file_id="f1", photo_path="/p1.jpg", points_awarded=50)
        
        # User 2: 30 Punkte
        user2 = crud.get_or_create_user(test_db, telegram_id=222222222)
        crud.create_submission(test_db, user_id=user2.id, submission_type=SubmissionType.PARTY_PHOTO,
                             photo_file_id="f2", photo_path="/p2.jpg", points_awarded=30)
        
        # User 3: 40 Punkte
        user3 = crud.get_or_create_user(test_db, telegram_id=333333333)
        crud.create_submission(test_db, user_id=user3.id, submission_type=SubmissionType.PARTY_PHOTO,
                             photo_file_id="f3", photo_path="/p3.jpg", points_awarded=40)
        
        # Rankings prüfen
        stats1 = crud.get_user_stats(test_db, 111111111)
        stats2 = crud.get_user_stats(test_db, 222222222)
        stats3 = crud.get_user_stats(test_db, 333333333)
        
        assert stats1["ranking"] == 1  # 50 Punkte
        assert stats3["ranking"] == 2  # 40 Punkte
        assert stats2["ranking"] == 3  # 30 Punkte
        assert stats1["total_users"] == 3
