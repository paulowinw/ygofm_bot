"""
Page Object Model (POM) Package.
Contains Chrome DOM wrappers and screen layout abstractions.
"""

from .base_page import BasePage
from .lobby_page import LobbyPage
from .game_board_page import GameBoardPage, GameState

__all__ = [
    "BasePage",
    "LobbyPage",
    "GameBoardPage",
    "GameState",
]
