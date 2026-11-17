"""
Summon Action for GameBoardPage.

Responsibilities:
- Handles Guardian Star selection modals when fusion monsters are summoned.
- Selects and confirms placement of monster cards onto player field zones.
"""

import time
from typing import Optional, Union
from ..base_action import BaseAction
from ...pages.game_board_page import GameBoardPage, GameState
from ...core.utils import log


class SummonAction(BaseAction):
    """
    Action that selects the Guardian Star and confirms monster field placement.
    """

    def __init__(self, page: GameBoardPage):
        super().__init__(page)

    @property
    def name(self) -> str:
        return "Summon"

    def execute(
        self,
        guardian_star: Union[str, int] = "Pluto",
        target_zone: int = 0,
        turn_number: int = 1,
    ) -> bool:
        """
        Handles guardian star prompt if present and confirms placement on field.
        """
        # 1. Check for Guardian Star prompt
        state = self.page.detect_screen_state()
        if state == GameState.GUARDIAN_STAR:
            self.page.choose_guardian_star(guardian_star, turn_number=turn_number)
            time.sleep(0.5)

        # 2. Check for Card Details recovery
        elif state == GameState.CARD_DETAILS:
            log("Card Details screen active during summon. Selecting FUSION to recover...", "WARN")
            self.page.select_fusion_on_card_details(turn_number=turn_number)
            time.sleep(0.5)

        # 3. Confirm monster placement on field
        current_state = self.page.detect_screen_state()
        if current_state not in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            self.page.place_monster_on_field(target_zone=target_zone, turn_number=turn_number)
            return True

        return False
