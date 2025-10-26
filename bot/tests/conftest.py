"""
Pytest Configuration und shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Bot module zum Python path hinzufügen
bot_dir = Path(__file__).parent.parent
sys.path.insert(0, str(bot_dir))


@pytest.fixture(scope="session")
def bot_root_dir():
    """Root Directory des Bots"""
    return Path(__file__).parent.parent


@pytest.fixture(scope="session")
def test_data_dir(bot_root_dir):
    """Directory für Test-Daten"""
    test_dir = bot_root_dir / "tests" / "test_data"
    test_dir.mkdir(exist_ok=True)
    return test_dir
