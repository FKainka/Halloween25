"""
Unit Tests für handlers
"""
import pytest
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from telegram import Update, User as TelegramUser, Message, Chat, PhotoSize, ReplyKeyboardMarkup
from telegram.ext import ContextTypes
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from database.models import Base, Team
from handlers.start import start_command, get_main_keyboard
from handlers.help import help_command
from handlers.points import points_command
from handlers.text import text_handler, handle_team_join
from handlers.photo import photo_handler
from handlers.film import film_command
from handlers.puzzle import puzzle_command


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
    
    def test_get_main_keyboard(self):
        """Test: Custom Keyboard erstellen"""
        keyboard = get_main_keyboard()
        
        assert isinstance(keyboard, ReplyKeyboardMarkup)
        assert keyboard.resize_keyboard == True
        assert keyboard.one_time_keyboard == False
    
    @pytest.mark.asyncio
    async def test_start_new_user(self, mock_update, mock_context, mock_db_session):
        """Test: /start für neuen User mit Custom Keyboard"""
        with patch('handlers.start.db') as mock_db:
            mock_db.get_session.return_value.__enter__.return_value = mock_db_session
            
            mock_bot = AsyncMock()
            mock_context.bot = mock_bot
            
            await start_command(mock_update, mock_context)
            
            # Prüfen dass send_message aufgerufen wurde
            assert mock_bot.send_message.called
            call_kwargs = mock_bot.send_message.call_args[1]
            
            # Prüfen dass reply_markup (Keyboard) enthalten ist
            assert 'reply_markup' in call_kwargs
            assert isinstance(call_kwargs['reply_markup'], ReplyKeyboardMarkup)
            
            # Prüfen dass Story-Text enthalten ist
            message_text = call_kwargs['text']
            assert "2097" in message_text or "Rebellion" in message_text
    
    @pytest.mark.asyncio
    async def test_start_admin_user(self, mock_update, mock_context, mock_db_session):
        """Test: /start für Admin"""
        with patch('handlers.start.db') as mock_db, \
             patch('handlers.start.config.is_admin') as mock_is_admin:
            
            mock_db.get_session.return_value.__enter__.return_value = mock_db_session
            mock_is_admin.return_value = True
            
            mock_bot = AsyncMock()
            mock_context.bot = mock_bot
            
            await start_command(mock_update, mock_context)
            
            assert mock_bot.send_message.called
            call_kwargs = mock_bot.send_message.call_args[1]
            message_text = call_kwargs['text']
            
            # Admin-Hinweis prüfen
            assert "Admin" in message_text


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
        """Test: Party Photo ohne Caption (1 Punkt)"""
        with patch('handlers.photo.db') as mock_db, \
             patch('handlers.photo.photo_manager') as mock_photo_mgr:
            
            mock_db.get_session.return_value.__enter__.return_value = mock_db_session
            mock_photo_mgr.save_photo.return_value = ("/path/photo.jpg", "/path/thumb.jpg")
            
            mock_bot = AsyncMock()
            mock_file = AsyncMock()
            mock_file.download_as_bytearray.return_value = bytearray(b"fake_image_data")
            mock_bot.get_file.return_value = mock_file
            mock_context.bot = mock_bot
            
            await photo_handler(mock_photo_update, mock_context)
            
            assert mock_bot.send_message.called
            call_kwargs = mock_bot.send_message.call_args[1]
            message_text = call_kwargs['text']
            
            # Bestätigung für Party Photo prüfen (1 Punkt)
            assert "1" in message_text
            assert "Punkt" in message_text or "Partyfoto" in message_text
    
    @pytest.mark.asyncio
    async def test_photo_with_command_caption_ignored(self, mock_photo_update, mock_context, mock_db_session):
        """Test: Foto mit /film Caption wird ignoriert (von film_command behandelt)"""
        mock_photo_update.message.caption = "/film Matrix"
        
        with patch('handlers.photo.db') as mock_db:
            mock_db.get_session.return_value.__enter__.return_value = mock_db_session
            
            mock_bot = AsyncMock()
            mock_context.bot = mock_bot
            
            await photo_handler(mock_photo_update, mock_context)
            
            # photo_handler soll nichts tun (Command-Handler übernimmt)
            assert not mock_bot.send_message.called


class TestFilmCommand:
    """Tests für /film Command"""
    
    @pytest.fixture
    def mock_film_update(self, mock_update):
        """Update mit /film Command und Foto"""
        photo = Mock(spec=PhotoSize)
        photo.file_id = "photo_file_123"
        photo.file_size = 50000
        
        mock_update.message.photo = [photo]
        mock_update.message.text = "/film Matrix"
        
        return mock_update
    
    @pytest.mark.asyncio
    async def test_film_without_photo(self, mock_update, mock_context):
        """Test: /film ohne Foto-Anhang"""
        mock_update.message.photo = None
        mock_update.message.text = "/film Matrix"
        
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        mock_context.args = ["Matrix"]
        
        await film_command(mock_update, mock_context)
        
        assert mock_bot.send_message.called
        call_kwargs = mock_bot.send_message.call_args[1]
        message_text = call_kwargs['text']
        
        # Fehlermeldung prüfen
        assert "Foto" in message_text
    
    @pytest.mark.asyncio
    async def test_film_without_title(self, mock_film_update, mock_context):
        """Test: /film ohne Film-Titel"""
        mock_context.args = []
        
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        await film_command(mock_film_update, mock_context)
        
        assert mock_bot.send_message.called
        call_kwargs = mock_bot.send_message.call_args[1]
        message_text = call_kwargs['text']
        
        # Fehlermeldung prüfen
        assert "Titel" in message_text or "Film-Titel" in message_text


class TestPuzzleCommand:
    """Tests für /puzzle Command"""
    
    @pytest.fixture
    def mock_puzzle_update(self, mock_update):
        """Update mit /puzzle Command und Screenshot"""
        photo = Mock(spec=PhotoSize)
        photo.file_id = "screenshot_123"
        photo.file_size = 100000
        
        mock_update.message.photo = [photo]
        mock_update.message.text = "/puzzle"
        
        return mock_update
    
    @pytest.mark.asyncio
    async def test_puzzle_without_photo(self, mock_update, mock_context):
        """Test: /puzzle ohne Screenshot"""
        mock_update.message.photo = None
        
        mock_bot = AsyncMock()
        mock_context.bot = mock_bot
        
        await puzzle_command(mock_update, mock_context)
        
        assert mock_bot.send_message.called
        call_kwargs = mock_bot.send_message.call_args[1]
        message_text = call_kwargs['text']
        
        # Fehlermeldung prüfen
        assert "Screenshot" in message_text
    
    @pytest.mark.asyncio
    async def test_puzzle_without_team(self, mock_puzzle_update, mock_context, mock_db_session):
        """Test: /puzzle ohne Team-Mitgliedschaft"""
        with patch('handlers.puzzle.db') as mock_db:
            mock_db.get_session.return_value.__enter__.return_value = mock_db_session
            
            mock_bot = AsyncMock()
            mock_context.bot = mock_bot
            
            await puzzle_command(mock_puzzle_update, mock_context)
            
            assert mock_bot.send_message.called
            call_kwargs = mock_bot.send_message.call_args[1]
            message_text = call_kwargs['text']
            
            # Fehlermeldung prüfen
            assert "Team" in message_text
