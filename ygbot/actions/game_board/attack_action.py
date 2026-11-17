"""
Attack Action for GameBoardPage.

Responsibilities:
- Executes combat attacks from a designated player monster zone to opponent zone / direct LP.
"""

from ..base_action import BaseAction
from ...pages.game_board_page import GameBoardPage, GameState
from ...core.utils import log


class AttackAction(BaseAction):
    """
    Action that selects a field monster and executes an attack sequence.
    """

    def __init__(self, page: GameBoardPage):
        super().__init__(page)

    @property
    def name(self) -> str:
        return "Attack"

    def execute(self, player_zone: int = 2, opponent_zone: int = 2, turn_number: int = 1) -> bool:
        """
        Executes attack if the board is not blocked by card details or modals.
        """
        state = self.page.detect_screen_state()
        if state in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            log(f"[Turn {turn_number}] Skipping attack: screen state is {state}.", "WARN")
            return False

        return self.page.execute_attack(
            player_zone=player_zone,
            opponent_zone=opponent_zone,
            turn_number=turn_number,
        )
