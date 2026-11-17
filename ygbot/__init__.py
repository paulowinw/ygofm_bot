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
from .pages.lobby_page import LobbyPage
from .pages.game_board_page import GameBoardPage, GameState
from .features.cards.card_manager import CardManager
from .actions.base_action import BaseAction
from .actions.game_board.inspect_hand_action import InspectHandAction
from .actions.game_board.fusion_action import FusionAction, FusionEngine
from .actions.game_board.summon_action import SummonAction
from .actions.game_board.attack_action import AttackAction
from .actions.game_board.end_turn_action import EndTurnAction
from .actions.lobby.start_duel_action import StartDuelAction

__all__ = [
    "YGBot",
    "Config",
    "CDPClient",
    "log",
    "Colors",
    "BasePage",
    "LobbyPage",
    "GameBoardPage",
    "GameState",
    "CardManager",
    "BaseAction",
    "InspectHandAction",
    "FusionAction",
    "FusionEngine",
    "SummonAction",
    "AttackAction",
    "EndTurnAction",
    "StartDuelAction",
]
