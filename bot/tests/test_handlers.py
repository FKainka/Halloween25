"""
Unit Tests für handlers
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User as TelegramUser, Message, Chat, PhotoSize
from telegram.ext import ContextTypes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Team
from handlers.start import start_command
from handlers.help import help_command
from handlers.points import points_command
from handlers.text import text_handler, handle_team_join
from handlers.photo import photo_handler


@pytest.fixture
def mock_db_session():
    """Mock Database Session"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    # Test-Teams
    team = Team(
        team_id=480514,
        film_title="Matrix",
        character_1="Trinity",
        character_2="Neo",
        character_1_id=246935,
        character_2_id=233579,
        puzzle_link="https://www.jigsawplanet.com/?rc=play&pid=matrix"
    )
    session.add(team)
    session.commit()
    
    yield session
    session.close()


@pytest.fixture
def mock_update():
    """Mock Telegram Update"""
    update = Mock(spec=Update)
    update.effective_user = Mock(spec=TelegramUser)
    update.effective_user.id = 123456789
    update.effective_user.username = "testuser"
    update.effective_user.first_name = "Test"
    update.effective_user.last_name = "User"
    
    update.message = Mock(spec=Message)
    update.message.reply_text = AsyncMock()
    update.message.chat = Mock(spec=Chat)
    update.message.chat.id = 123456789
    
    return update


@pytest.fixture
def mock_context():
    """Mock Telegram Context"""
    context = Mock(spec=ContextTypes.DEFAULT_TYPE)
    return context


class TestStartHandler:
    """Tests für /start Command"""
    
    @pytest.mark.asyncio
    async def test_start_new_user(self, mock_update, mock_context, mock_db_session):
        """Test: /start für neuen User"""
        with patch('handlers.start.Database') as mock_db:
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            
            await start_command(mock_update, mock_context)
            
            # Prüfen dass reply_text aufgerufen wurde
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Prüfen dass Story-Text enthalten ist
            assert "2097" in call_args
            assert "KI" in call_args or "Simulation" in call_args
    
    @pytest.mark.asyncio
    async def test_start_admin_user(self, mock_update, mock_context, mock_db_session):
        """Test: /start für Admin"""
        with patch('handlers.start.Database') as mock_db, \
             patch('handlers.start.config.is_admin') as mock_is_admin:
            
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            mock_is_admin.return_value = True
            
            await start_command(mock_update, mock_context)
            
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Admin-Hinweis prüfen
            assert "Admin" in call_args


class TestHelpHandler:
    """Tests für /help Command"""
    
    @pytest.mark.asyncio
    async def test_help_command(self, mock_update, mock_context):
        """Test: /help zeigt Spielregeln"""
        await help_command(mock_update, mock_context)
        
        assert mock_update.message.reply_text.called
        call_args = mock_update.message.reply_text.call_args[0][0]
        
        # Prüfen dass wichtige Infos enthalten sind
        assert "Punkte" in call_args or "Photo" in call_args or "Foto" in call_args


class TestPointsHandler:
    """Tests für /punkte Command"""
    
    @pytest.mark.asyncio
    async def test_points_new_user(self, mock_update, mock_context, mock_db_session):
        """Test: /punkte für User ohne Punkte"""
        with patch('handlers.points.Database') as mock_db:
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            
            await points_command(mock_update, mock_context)
            
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Prüfen dass 0 Punkte angezeigt werden
            assert "0" in call_args


class TestTextHandler:
    """Tests für Text Message Handler (Team Join)"""
    
    @pytest.mark.asyncio
    async def test_team_join_valid(self, mock_update, mock_context, mock_db_session):
        """Test: Gültiger Team-Beitritt"""
        mock_update.message.text = "Team: 480514"
        
        with patch('handlers.text.Database') as mock_db:
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            
            await text_handler(mock_update, mock_context)
            
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Erfolgsmeldung prüfen
            assert "Matrix" in call_args or "Team" in call_args
            assert "25" in call_args  # Punkte
    
    @pytest.mark.asyncio
    async def test_team_join_invalid_format(self, mock_update, mock_context, mock_db_session):
        """Test: Ungültiges Format"""
        mock_update.message.text = "Team: abc123"
        
        with patch('handlers.text.Database') as mock_db:
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            
            await text_handler(mock_update, mock_context)
            
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Fehlermeldung prüfen
            assert "falsch" in call_args.lower() or "ungültig" in call_args.lower()
    
    @pytest.mark.asyncio
    async def test_team_join_invalid_id(self, mock_update, mock_context, mock_db_session):
        """Test: Nicht existierende Team-ID"""
        mock_update.message.text = "Team: 999999"
        
        with patch('handlers.text.Database') as mock_db:
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            
            await text_handler(mock_update, mock_context)
            
            assert mock_update.message.reply_text.called
            call_args = mock_update.message.reply_text.call_args[0][0]
            
            # Fehlermeldung prüfen
            assert "nicht gefunden" in call_args.lower() or "existiert nicht" in call_args.lower()


class TestPhotoHandler:
    """Tests für Photo Upload Handler"""
    
    @pytest.fixture
    def mock_photo_update(self, mock_update):
        """Update mit Photo"""
        photo = Mock(spec=PhotoSize)
        photo.file_id = "photo_file_123"
        photo.file_size = 50000
        
        mock_update.message.photo = [photo]
        mock_update.message.caption = None
        
        return mock_update
    
    @pytest.mark.asyncio
    async def test_party_photo_no_caption(self, mock_photo_update, mock_context, mock_db_session):
        """Test: Party Photo ohne Caption"""
        with patch('handlers.photo.Database') as mock_db, \
             patch('handlers.photo.photo_manager') as mock_photo_mgr, \
             patch('handlers.photo.context') as mock_bot_context:
            
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            mock_photo_mgr.save_photo.return_value = ("/path/photo.jpg", "/path/thumb.jpg")
            mock_bot = AsyncMock()
            mock_bot.get_file.return_value = AsyncMock()
            mock_bot_context.bot = mock_bot
            
            await photo_handler(mock_photo_update, mock_context)
            
            assert mock_photo_update.message.reply_text.called
            call_args = mock_photo_update.message.reply_text.call_args[0][0]
            
            # Bestätigung für Party Photo prüfen
            assert "1" in call_args  # 1 Punkt
    
    @pytest.mark.asyncio
    async def test_film_reference_with_caption(self, mock_photo_update, mock_context, mock_db_session):
        """Test: Film Reference mit Caption"""
        mock_photo_update.message.caption = "Film: Matrix"
        
        with patch('handlers.photo.Database') as mock_db, \
             patch('handlers.photo.photo_manager') as mock_photo_mgr, \
             patch('handlers.photo.context') as mock_bot_context:
            
            mock_db.return_value.get_session.return_value.__enter__.return_value = mock_db_session
            mock_photo_mgr.save_photo.return_value = ("/path/photo.jpg", "/path/thumb.jpg")
            mock_bot = AsyncMock()
            mock_bot.get_file.return_value = AsyncMock()
            mock_bot_context.bot = mock_bot
            
            await photo_handler(mock_photo_update, mock_context)
            
            assert mock_photo_update.message.reply_text.called
            call_args = mock_photo_update.message.reply_text.call_args[0][0]
            
            # Bestätigung für Film prüfen
            assert "20" in call_args or "Film" in call_args
