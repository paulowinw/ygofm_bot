"""
Yu-Gi-Oh! Forbidden Memories Online Auto-Dueler Bot (YGBot)
"""

__version__ = "1.0.0"
__author__ = "Antigravity"

from .board_interaction import BoardInteraction
from .bot import YGBot
from .game_interface import GameInterface, GameState
from .cdp_client import CDPClient
from .config import Config

__all__ = [
    "BoardInteraction",
    "YGBot",
    "GameInterface",
    "GameState",
    "CDPClient",
    "Config",
]
