"""
End Turn Action for GameBoardPage.

Responsibilities:
- Safely ends the player's turn using the 'e' shortcut key.
"""

from ..base_action import BaseAction
from ...pages.game_board_page import GameBoardPage, GameState


class EndTurnAction(BaseAction):
    """
    Action that ends the player's turn.
    """

    def __init__(self, page: GameBoardPage):
        super().__init__(page)

    @property
    def name(self) -> str:
        return "EndTurn"

    def execute(self, turn_number: int = 1) -> bool:
        """
        Dispatches end turn command.
        """
        state = self.page.detect_screen_state()
        if state == GameState.SURRENDER_PROMPT:
            self.page.dismiss_surrender_modal(turn_number=turn_number)

        return self.page.end_turn(turn_number=turn_number)
