"""
Lobby Page Object for Yu-Gi-Oh! Forbidden Memories Online.

Adapted Page Object Model (POM):
Encapsulates DOM interactions, opponent selection, and duel matchmaking buttons
for the Free Duel lobby and result screens.
"""

from typing import Optional
from .base_page import BasePage
from ..core.utils import log, Colors


class LobbyPage(BasePage):
    """
    Page Object representing the Free Duel lobby and match selection screen.
    """

    def select_opponent(self, opponent_name: str, turn_number: Optional[int] = None) -> bool:
        """Selects an opponent card or button in the Free Duel lobby."""
        t = turn_number or 1
        log(f"Lobby: Selecting opponent '{Colors.BOLD}{opponent_name}{Colors.END}'...", "INFO")
        return self.click(
            text=opponent_name,
            description=f"Select Opponent '{opponent_name}'",
            turn_number=t,
        )

    def click_start_duel(self, turn_number: Optional[int] = None) -> bool:
        """Clicks the START DUEL button."""
        t = turn_number or 1
        return self.click(
            text="START DUEL",
            description="Click 'START DUEL'",
            turn_number=t,
        )

    def start_duel(self, opponent_name: str, turn_number: Optional[int] = None) -> bool:
        """Selects opponent and clicks START DUEL to begin a match."""
        t = turn_number or 1
        if self.click_start_duel(turn_number=t):
            return True
        return self.select_opponent(opponent_name=opponent_name, turn_number=t)

    def click_duel_again(self, turn_number: Optional[int] = None) -> bool:
        """Clicks the DUEL AGAIN button on the victory/defeat summary screen."""
        t = turn_number or 1
        bx, by = getattr(self.cfg, "duel_again_button", [0.448, 0.588])
        if self.click(text="DUEL AGAIN", description="Click 'DUEL AGAIN' button", turn_number=t):
            return True
        return self.click(x=bx, y=by, description="Click DUEL AGAIN by coordinate", turn_number=t)
