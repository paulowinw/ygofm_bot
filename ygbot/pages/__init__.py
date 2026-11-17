"""
Pages package implementing the Adapted Page Object Model (POM).
"""

from .base_page import BasePage
from .game_board_page import GameBoardPage, GameState

__all__ = ["BasePage", "GameBoardPage", "GameState"]
