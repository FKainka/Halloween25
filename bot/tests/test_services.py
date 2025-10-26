"""
Unit Tests für Services (photo_manager, template_manager, yaml_loader)
"""
import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from PIL import Image
import io

from services.photo_manager import PhotoManager
from services.template_manager import TemplateManager
from utils.yaml_loader import UniverseLoader


class TestPhotoManager:
    """Tests für PhotoManager"""
    
    @pytest.fixture
    def photo_manager(self, tmp_path):
        """PhotoManager mit temp directory"""
        return PhotoManager(base_path=tmp_path)
    
    @pytest.fixture
    def mock_photo_file(self):
        """Mock Photo File"""
        # Kleines Test-Bild erstellen
        img = Image.new('RGB', (800, 600), color='red')
        img_bytes = io.BytesIO()
        img.save(img_bytes, format='JPEG')
        img_bytes.seek(0)
        return img_bytes
    
    def test_save_photo_party(self, photo_manager, mock_photo_file, tmp_path):
        """Test: Party Photo speichern"""
        photo_path, thumb_path = photo_manager.save_photo(
            file_bytes=mock_photo_file.read(),
            user_id=123456789,
            submission_id=1,
            category="party"
        )
        
        # Prüfen dass Dateien erstellt wurden
        assert Path(photo_path).exists()
        assert Path(thumb_path).exists()
        
        # Prüfen dass Ordner korrekt ist
        assert "party" in photo_path
        
        # Prüfen dass Thumbnail kleiner ist
        thumb_img = Image.open(thumb_path)
        assert thumb_img.size[0] <= 200
        assert thumb_img.size[1] <= 200
    
    def test_save_photo_film(self, photo_manager, mock_photo_file, tmp_path):
        """Test: Film Photo speichern"""
        mock_photo_file.seek(0)
        photo_path, thumb_path = photo_manager.save_photo(
            file_bytes=mock_photo_file.read(),
            user_id=123456789,
            submission_id=2,
            category="films",
            subcategory="Matrix"
        )
        
        assert Path(photo_path).exists()
        assert "films" in photo_path
        assert "Matrix" in photo_path
    
    def test_save_photo_puzzle(self, photo_manager, mock_photo_file, tmp_path):
        """Test: Puzzle Photo speichern"""
        mock_photo_file.seek(0)
        photo_path, thumb_path = photo_manager.save_photo(
            file_bytes=mock_photo_file.read(),
            user_id=123456789,
            submission_id=3,
            category="puzzles"
        )
        
        assert Path(photo_path).exists()
        assert "puzzles" in photo_path


class TestTemplateManager:
    """Tests für TemplateManager"""
    
    @pytest.fixture
    def template_manager(self, tmp_path):
        """TemplateManager mit temp templates"""
        templates_dir = tmp_path / "templates"
        templates_dir.mkdir()
        
        # Test-Templates erstellen
        (templates_dir / "welcome.txt").write_text(
            "Willkommen {{ first_name }}! {% if is_admin %}Admin!{% endif %}"
        )
        (templates_dir / "help.txt").write_text("Hilfe für das Spiel")
        (templates_dir / "points.txt").write_text(
            "Du hast {{ total_points }} Punkte. Rang: {{ ranking }}"
        )
        (templates_dir / "team_joined.txt").write_text(
            "Team {{ team_name }} beigetreten! +{{ points }} Punkte. Puzzle: {{ puzzle_link }}"
        )
        
        return TemplateManager(templates_path=templates_dir)
    
    def test_render_welcome(self, template_manager):
        """Test: Welcome Template rendern"""
        result = template_manager.render_welcome("Max", is_admin=False)
        
        assert "Willkommen Max" in result
        assert "Admin" not in result
    
    def test_render_welcome_admin(self, template_manager):
        """Test: Welcome Template für Admin"""
        result = template_manager.render_welcome("Admin", is_admin=True)
        
        assert "Willkommen Admin" in result
        assert "Admin!" in result
    
    def test_render_help(self, template_manager):
        """Test: Help Template rendern"""
        result = template_manager.render_help()
        
        assert "Hilfe" in result
    
    def test_render_points(self, template_manager):
        """Test: Points Template rendern"""
        result = template_manager.render_points(
            total_points=50,
            party_points=10,
            film_points=20,
            team_points=20,
            puzzle_points=0,
            party_photos_count=10,
            film_count=1,
            team_name="Matrix",
            recognized_films=["Matrix"],
            ranking=3,
            total_users=15
        )
        
        assert "50 Punkte" in result
        assert "Rang: 3" in result
    
    def test_render_team_joined(self, template_manager):
        """Test: Team Joined Template rendern"""
        result = template_manager.render_team_joined(
            team_name="Matrix",
            points=25,
            puzzle_link="https://puzzle.com"
        )
        
        assert "Matrix" in result
        assert "25 Punkte" in result
        assert "https://puzzle.com" in result


class TestUniverseLoader:
    """Tests für UniverseLoader (YAML)"""
    
    @pytest.fixture
    def mock_yaml_content(self):
        """Mock YAML Content"""
        return """
Universen:
  - Film: Matrix
    Charaktere:
      - Name: Trinity
        ID: 246935
      - Name: Neo
        ID: 233579
    "Puzzle-Link": "https://www.jigsawplanet.com/?rc=play&pid=matrix"
  
  - Film: Terminator
    Charaktere:
      - Name: Sarah Connor
        ID: 250000
      - Name: John Connor
        ID: 250000
    "Puzzle-Link": "https://www.jigsawplanet.com/?rc=play&pid=terminator"
"""
    
    def test_load_yaml(self, mock_yaml_content, tmp_path):
        """Test: YAML laden"""
        yaml_file = tmp_path / "universen.yaml"
        yaml_file.write_text(mock_yaml_content)
        
        loader = UniverseLoader(yaml_path=yaml_file)
        loader.load()
        
        assert loader.data is not None
        assert "Universen" in loader.data
    
    def test_get_teams(self, mock_yaml_content, tmp_path):
        """Test: Teams aus YAML extrahieren"""
        yaml_file = tmp_path / "universen.yaml"
        yaml_file.write_text(mock_yaml_content)
        
        loader = UniverseLoader(yaml_path=yaml_file)
        loader.load()
        teams = loader.get_teams()
        
        assert len(teams) == 2
        
        # Matrix Team prüfen
        matrix_team = teams[0]
        assert matrix_team["film_title"] == "Matrix"
        assert matrix_team["team_id"] == 480514  # 246935 + 233579
        assert matrix_team["character_1"] == "Trinity"
        assert matrix_team["character_2"] == "Neo"
        assert "puzzle_link" in matrix_team
    
    def test_get_films(self, mock_yaml_content, tmp_path):
        """Test: Film-Liste extrahieren"""
        yaml_file = tmp_path / "universen.yaml"
        yaml_file.write_text(mock_yaml_content)
        
        loader = UniverseLoader(yaml_path=yaml_file)
        loader.load()
        films = loader.get_films()
        
        assert len(films) == 2
        assert "Matrix" in films
        assert "Terminator" in films


class TestIntegration:
    """Integration Tests für komplette Workflows"""
    
    def test_complete_user_flow(self):
        """Test: Kompletter User-Flow von Registration bis Points"""
        # Dieser Test würde den kompletten Flow durchlaufen:
        # 1. User registriert sich (/start)
        # 2. User lädt Party Photo hoch (+1 Punkt)
        # 3. User sendet Team-Text (+25 Punkte)
        # 4. User lädt Puzzle-Photo hoch (+25 Punkte)
        # 5. User prüft Punkte (/punkte)
        # 
        # Wird hier nur als Beispiel beschrieben, da es komplexe Mocks erfordert
        pass
