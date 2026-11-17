"""
Start Duel Action for Lobby interactions.

Responsibilities:
- Searches for and selects campaign/free duel opponents on the LobbyPage.
- Clicks the START DUEL button.
"""

from typing import Any
from ..base_action import BaseAction
from ...core.utils import log, Colors


class StartDuelAction(BaseAction):
    """
    Action that selects an opponent and initiates a duel from the lobby.
    """

    def __init__(self, page: Any):
        super().__init__(page)

    @property
    def name(self) -> str:
        return "StartDuel"

    def execute(self, opponent_name: str, turn_number: int = 1) -> bool:
        """
        Clicks opponent and START DUEL on the lobby screen.
        """
        log(f"Lobby: Initiating duel against {Colors.BOLD}{opponent_name}{Colors.END}...", "INFO")
        if hasattr(self.page, "start_duel"):
            return self.page.start_duel(opponent_name=opponent_name, turn_number=turn_number)
        if hasattr(self.page, "start_duel_from_lobby"):
            return self.page.start_duel_from_lobby(opponent_name=opponent_name, turn_number=turn_number)
        return False
