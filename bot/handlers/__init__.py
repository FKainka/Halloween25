"""
Handler __init__.py
Exportiert alle Command-Handler.
"""

from handlers.start import start_command
from handlers.help import help_command
from handlers.points import points_command
from handlers.photo import photo_handler
from handlers.text import text_handler
from handlers.team import team_command
from .admin import (
    admin_help_command,
    admin_command,
    admin_players_command,
    admin_player_command,
    admin_teams_command,
    admin_stats_command,
    admin_points_command,
    admin_eastereggs_command
)

__all__ = [
    'start_command',
    'help_command', 
    'points_command',
    'photo_handler',
    'text_handler',
    'team_command',
    'admin_command',
    'admin_players_command',
    'admin_player_command',
    'admin_teams_command',
    'admin_stats_command',
    'admin_points_command',
    'admin_eastereggs_command'
]
