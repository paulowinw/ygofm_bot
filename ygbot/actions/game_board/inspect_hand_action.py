"""
Inspect Hand Action for GameBoardPage.

Responsibilities:
- When the board opens for the first time, navigates cards one by one using keyboard:
  * Presses ArrowDown to go to the first card.
  * Presses Enter to show card details in the opened box.
  * Extracts optimal card data (name, ATK, DEF, type, Guardian Star) from the opened box.
  * Presses Esc to close the card box.
  * Presses ArrowRight to focus the next card.
- Stores verified Card domain models into a variable to perform fusions after having all card info in hand.
- Prints the cards in hand into a formatted console table.
"""

from typing import List, Optional, Dict, Any
from ..base_action import BaseAction
from ...pages.game_board_page import GameBoardPage
from ...features.cards.models import Card, MonsterCard, EquipCard
from ...features.cards.card_manager import CardManager
from ...core.utils import log, print_cards_table


class InspectHandAction(BaseAction):
    """
    Action that inspects each hand card one by one when the board opens,
    stores card data for fusion processing, and prints a formatted table to stdout.
    """

    def __init__(self, page: GameBoardPage, card_manager: Optional[CardManager] = None):
        super().__init__(page)
        self.card_manager = card_manager or CardManager()
        self.cards_in_hand: List[Card] = []
        self.has_inspected_initial_board: bool = False

    @property
    def name(self) -> str:
        return "InspectHand"

    def reset(self):
        """Resets the inspected card state for a new duel."""
        self.cards_in_hand = []
        self.has_inspected_initial_board = False

    def execute(self, turn_number: int = 1) -> List[Card]:
        """
        When the board opens, navigates across cards one by one using keyboard:
        1. Press ArrowDown -> goes to the first card (slot 0).
        2. For each card (slots 0..4):
           - Press Enter -> opens the card details box showing optimal card details.
           - Extract optimal card data (name, atk, def, type, guardian star) from the opened box.
           - Press Esc (Escape) -> closes the card box.
           - If not the last card (slot < 4):
               Press ArrowRight -> focus the next card.
        3. Store verified cards in memory variable `self.cards_in_hand` for subsequent fusion evaluation.
        4. Print the verified cards into a formatted table on the console.
        """
        log(f"[Turn {turn_number}] Inspecting hand: opening cards one by one...", "DUEL")
        hand_cards: List[Card] = []

        # 1. When the board opens, press ArrowDown to go to the first card (Slot 0)
        self.page.focus_hand(turn_number=turn_number)

        for slot_idx in range(5):
            # 2. Press Enter to show the info of the card in the opened card box
            self.page.open_card_details(turn_number=turn_number)

            # 3. Read optimal card details from the opened box
            raw_data = self.page.read_opened_card_details(slot_index=slot_idx, turn_number=turn_number)
            card_name = raw_data.get("name") or f"Card {slot_idx + 1}"

            # 4. Convert to rich domain model via CardRegistry
            card = self.card_manager.registry.create_card_from_name(card_name, index=slot_idx)

            # Augment with optimal stats from the opened box
            if isinstance(card, MonsterCard):
                if raw_data.get("atk") is not None:
                    card.atk = int(raw_data["atk"])
                if raw_data.get("def") is not None:
                    card.def_ = int(raw_data["def"])
                if raw_data.get("star"):
                    card.guardian_star_primary = raw_data["star"]

            hand_cards.append(card)

            # 5. Press Esc to close the card box
            self.page.close_card_details(turn_number=turn_number)

            # 6. If not the last card, press ArrowRight to focus the next card
            if slot_idx < 4:
                self.page.focus_next_hand_card(turn_number=turn_number)

        # Store in variable for subsequent fusion evaluation
        self.cards_in_hand = hand_cards
        self.card_manager.current_hand = hand_cards
        self.has_inspected_initial_board = True

        # Print the cards in hand into a formatted table on the console
        print_cards_table(self.cards_in_hand, title=f"TURN {turn_number} - HAND CARDS INSPECTED")

        return self.cards_in_hand
