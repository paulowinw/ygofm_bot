"""
Fusion Engine for Yu-Gi-Oh! Forbidden Memories.

Design Pattern: Context in Strategy Pattern
Coordinates card evaluation and requests card interactions through
the Page Object (game_board_page.py).
"""

from typing import List, Dict, Optional, Tuple, Union, Any
from ..cards.models import Card
from ..cards.registry import CardRegistry
from .result import FusionResult
from .strategies import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)


class FusionEngine:
    """
    Context class that coordinates card normalization, delegates fusion solving
    to a pipeline of FusionStrategy implementations, and requests card interactions
    from the GameBoardPage.
    """

    def __init__(self, strategy: str = "THTD", registry: Optional[CardRegistry] = None):
        self.strategy_name = strategy
        self.registry = registry or CardRegistry.get_instance()
        self.strategies: List[FusionStrategy] = self._build_strategies(strategy)

    def _build_strategies(self, strategy_name: str) -> List[FusionStrategy]:
        """Builds the ordered evaluation chain of strategies."""
        name_clean = strategy_name.strip().lower() if strategy_name else "thtd"

        if name_clean == "highest_atk":
            return [
                HighestAtkStrategy(),
                MeteorBlackDragonStrategy(),
                THTDFusionStrategy(),
                DiscardAndCycleStrategy(),
                EquipBuffStrategy(),
                ElementalFusionStrategy(),
            ]

        return [
            MeteorBlackDragonStrategy(),
            THTDFusionStrategy(),
            DiscardAndCycleStrategy(),
            EquipBuffStrategy(),
            ElementalFusionStrategy(),
            HighestAtkStrategy(),
        ]

    def register_strategy(self, strategy: FusionStrategy, prepend: bool = False):
        """Registers a custom strategy at runtime (Open/Closed Principle)."""
        if prepend:
            self.strategies.insert(0, strategy)
        else:
            self.strategies.append(strategy)

    def solve_hand(self, hand: List[Union[str, Dict[str, Any], Card]]) -> FusionResult:
        """
        Given a hand of cards, normalizes them into Card domain models
        and evaluates strategies in priority order.
        """
        if not hand:
            return FusionResult(sequence=[], play_name="Empty Hand", estimated_atk=0)

        card_models: List[Card] = [
            self.registry.from_any(item, index=i)
            for i, item in enumerate(hand)
        ]

        for strategy in self.strategies:
            result = strategy.evaluate(card_models)
            if result is not None:
                return result

        first_card = card_models[0]
        return FusionResult(
            sequence=[0],
            play_name=first_card.name,
            estimated_atk=getattr(first_card, "atk", 1000),
        )

    def execute_fusion(self, result: FusionResult, board_page: Any, turn_number: int = 1) -> bool:
        """
        Requests specific card interactions from the Page Object (GameBoardPage).
        Finds and clicks/selects the cards in sequence, then triggers the fusion.
        """
        if not result.sequence:
            return False

        # Ask the Page Object to interact with each card in the fusion sequence
        for slot in result.sequence:
            board_page.click_card_at_slot(slot, turn_number=turn_number)

        # Trigger fusion confirmation on the board
        return board_page.trigger_fusion(turn_number=turn_number)
