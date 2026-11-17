"""
Yu-Gi-Oh! Forbidden Memories Fusion Solver Engine.

Design Pattern: Context in Strategy Pattern
- The FusionEngine class acts as the Context.
- It is configured with an ordered sequence of FusionStrategy objects.
- It decouples the client (e.g. YGBot) from the specific fusion algorithms
  and card data structures.
- It accepts hands in any supported format (Card objects, card name strings, or raw dicts),
  normalizes them using the CardRegistry Factory, and delegates hand solving to its strategies.
"""

from typing import List, Dict, Optional, Tuple, Union, Any
from ..cards import Card, CardRegistry
from .strategy import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)
from .result import FusionResult


class FusionEngine:
    """
    Context class that coordinates card normalization and delegates fusion solving
    to a pipeline of FusionStrategy implementations.
    """

    def __init__(self, strategy: str = "THTD", registry: Optional[CardRegistry] = None):
        """
        Initializes the FusionEngine.
        
        Args:
            strategy: High-level strategy profile ("THTD", "highest_atk").
            registry: Optional custom CardRegistry instance (uses singleton if None).
        """
        self.strategy_name = strategy
        self.registry = registry or CardRegistry.get_instance()
        self.strategies: List[FusionStrategy] = self._build_strategies(strategy)

    def _build_strategies(self, strategy_name: str) -> List[FusionStrategy]:
        """
        Factory helper that builds the ordered evaluation chain of strategies
        based on user configuration.
        """
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
        
        # Default prioritized farming: Meteor Black Dragon -> THTD -> Discard/Cycle -> Secondary
        return [
            MeteorBlackDragonStrategy(),
            THTDFusionStrategy(),
            DiscardAndCycleStrategy(),
            EquipBuffStrategy(),
            ElementalFusionStrategy(),
            HighestAtkStrategy(),
        ]

    def register_strategy(self, strategy: FusionStrategy, prepend: bool = False):
        """
        Allows dynamically injecting a custom FusionStrategy at runtime.
        Demonstrates the Open/Closed Principle enabled by the Strategy Pattern.
        """
        if prepend:
            self.strategies.insert(0, strategy)
        else:
            self.strategies.append(strategy)

    def identify_card(self, card_name: str) -> Dict[str, Any]:
        """
        Looks up or infers card attributes.
        Provided for backward compatibility with existing codebase.
        """
        card = self.registry.create_card_from_name(card_name)
        return card.to_dict()

    def solve_hand(self, hand: List[Union[str, Dict[str, Any], Card]]) -> FusionResult:
        """
        Given a hand of cards (each item can be a Card, a dict, or a card name string),
        normalizes the cards and iterates through the strategy chain until a match is found.
        
        Returns:
            FusionResult containing (sequence, outcome_name, estimated_atk).
            Can be unpacked directly: sequence, name, atk = engine.solve_hand(hand)
        """
        if not hand:
            return FusionResult(sequence=[], play_name="Empty Hand", estimated_atk=0)

        # 1. Normalize all inputs into typed Card domain models
        card_models: List[Card] = [
            self.registry.from_any(item, index=i)
            for i, item in enumerate(hand)
        ]

        # 2. Iterate through strategies in priority order (Strategy Pattern)
        for strategy in self.strategies:
            result = strategy.evaluate(card_models)
            if result is not None:
                return result

        # 3. Ultimate fallback
        first_card = card_models[0]
        return FusionResult(
            sequence=[0],
            play_name=first_card.name,
            estimated_atk=getattr(first_card, "atk", 1000),
        )
