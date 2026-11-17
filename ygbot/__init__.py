"""
Yu-Gi-Oh! Forbidden Memories Online Auto-Dueler Bot (YGBot)
"""

__version__ = "1.0.0"
__author__ = "Antigravity"

from .bot import YGBot
from .core.config import Config
from .core.cdp_client import CDPClient
from .core.utils import log, Colors
from .pages.base_page import BasePage
from .pages.game_board_page import GameBoardPage, GameState
from .features.cards.card_manager import CardManager
from .features.fusion.engine import FusionEngine

__all__ = [
    "YGBot",
    "Config",
    "CDPClient",
    "log",
    "Colors",
    "BasePage",
    "GameBoardPage",
    "GameState",
    "CardManager",
    "FusionEngine",
]
