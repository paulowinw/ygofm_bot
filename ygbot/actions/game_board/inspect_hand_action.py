"""
Inspect Hand Action for GameBoardPage.

Responsibilities:
- When the board opens for the first time, navigates cards one by one using keyboard:
  * Presses ArrowDown to go to the first card (Slot 1 / index 0).
  * Traverses the board opening sequence: Slot 1 -> Slot 3 -> Slot 5 -> Slot 2 -> Slot 4.
  * Presses Enter to show card details in the opened box.
  * Extracts optimal card data (name, ATK, DEF, type, Guardian Star) from the opened box.
  * Presses Esc to close the card box.
  * Presses ArrowRight to focus the next card in navigation sequence.
- Maps inspected cards to their true physical board slots (0..4).
- Stores verified Card domain models into variable `self.cards_in_hand` (ordered by Slot 1..5)
  to perform fusions after having all card info in hand.
- Prints the cards in hand into a formatted table on the console (ordered by Slot 1..5).
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

    Slot Traversal Sequence:
    In the duel arena, keyboard navigation traverses the hand in order:
    Slot 1 -> Slot 3 -> Slot 5 -> Slot 2 -> Slot 4 (0-indexed: [0, 2, 4, 1, 3]).

    The inspected cards are mapped to their true physical board slots (0..4)
    so that self.cards_in_hand and the console table accurately reflect Slot 1 through Slot 5.
    """

    # Physical slot indices visited in order during board navigation:
    # 0 = Slot 1, 2 = Slot 3, 4 = Slot 5, 1 = Slot 2, 3 = Slot 4
    DEFAULT_SLOT_SEQUENCE = [0, 2, 4, 1, 3]

    def __init__(
        self,
        page: GameBoardPage,
        card_manager: Optional[CardManager] = None,
        slot_sequence: Optional[List[int]] = None,
    ):
        super().__init__(page)
        self.card_manager = card_manager or CardManager()
        self.slot_sequence: List[int] = list(slot_sequence) if slot_sequence is not None else list(self.DEFAULT_SLOT_SEQUENCE)
        self.cards_in_hand: List[Card] = []
        self.opened_sequence: List[Card] = []
        self.has_inspected_initial_board: bool = False

    @property
    def name(self) -> str:
        return "InspectHand"

    def reset(self):
        """Resets the inspected card state for a new duel."""
        self.cards_in_hand = []
        self.opened_sequence = []
        self.has_inspected_initial_board = False

    def execute(self, turn_number: int = 1) -> List[Card]:
        """
        When the board opens, navigates across cards one by one using keyboard:
        1. Press ArrowDown -> goes to the first card (Slot 1 / index 0).
        2. For each card in the slot navigation sequence (Slots 1, 3, 5, 2, 4):
           - Press Enter -> opens the card details box showing optimal card details.
           - Extract optimal card data (name, atk, def, type, guardian star) for target_slot.
           - Convert to rich Card domain model with index=target_slot.
           - Place card into hand_cards at its true physical slot: hand_cards[target_slot] = card.
           - Press Esc (Escape) -> closes the card box.
           - If not the last card in sequence:
               Press ArrowRight -> focus the next card in navigation sequence.
        3. Store verified cards in memory variable `self.cards_in_hand` (ordered by Slot 1..5)
           for subsequent fusion evaluation.
        4. Print the verified cards into a formatted table on the console (ordered by Slot 1..5).
        """
        log(f"[Turn {turn_number}] Inspecting hand: opening cards one by one...", "DUEL")
        
        slot_count = max(max(self.slot_sequence) + 1, len(self.slot_sequence), 5)
        hand_cards: List[Optional[Card]] = [None] * slot_count
        opened_sequence: List[Card] = []

        # 1. When the board opens, press ArrowDown to go to the first card (Slot 1 / index 0)
        self.page.focus_hand(turn_number=turn_number)

        total_steps = len(self.slot_sequence)
        for step, target_slot in enumerate(self.slot_sequence):
            # 2. Press Enter to show the info of the card in the opened card box
            self.page.open_card_details(turn_number=turn_number)

            # 3. Read optimal card details from the opened box for target_slot
            raw_data = self.page.read_opened_card_details(slot_index=target_slot, turn_number=turn_number)
            card_name = raw_data.get("name") or f"Card {target_slot + 1}"

            # 4. Convert to rich domain model via CardRegistry with index=target_slot
            card = self.card_manager.registry.create_card_from_name(card_name, index=target_slot)

            # Augment with optimal stats from the opened box
            if isinstance(card, MonsterCard):
                if raw_data.get("atk") is not None:
                    card.atk = int(raw_data["atk"])
                if raw_data.get("def") is not None:
                    card.def_ = int(raw_data["def"])
                if raw_data.get("star"):
                    card.guardian_star_primary = raw_data["star"]

            # Store card at its true physical slot position
            hand_cards[target_slot] = card
            opened_sequence.append(card)

            # 5. Press Esc to close the card box
            self.page.close_card_details(turn_number=turn_number)

            # 6. If not the last card, press ArrowRight to focus the next card
            if step < total_steps - 1:
                next_slot = self.slot_sequence[step + 1]
                try:
                    self.page.focus_next_hand_card(target_slot=next_slot, turn_number=turn_number)
                except TypeError:
                    self.page.focus_next_hand_card(turn_number=turn_number)
                    if hasattr(self.page, "current_hand_slot"):
                        self.page.current_hand_slot = next_slot

        # Finalize hand ordered by slot (0..4)
        ordered_hand = [c for c in hand_cards if c is not None]
        self.cards_in_hand = ordered_hand
        self.opened_sequence = opened_sequence
        self.card_manager.current_hand = ordered_hand
        self.has_inspected_initial_board = True

        # Print the cards in hand into a formatted table on the console (ordered by Slot 1..5)
        print_cards_table(self.cards_in_hand, title=f"TURN {turn_number} - HAND CARDS INSPECTED")

        return self.cards_in_hand
