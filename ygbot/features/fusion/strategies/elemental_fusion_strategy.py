"""
Elemental Archetype Pairwise Fusion Strategy.

Artifact: Concrete Strategy
Priority: 5 (Classic Elemental Secondary Fusions)
Handles classic secondary high-tier recipes in Forbidden Memories:
- Dragon + Plant -> Black Forest Dragon (2100 ATK)
- Beast + Pyro -> Flame Cerebrus (2100 ATK)
- Rock + Female -> Mystical Sand (2100 ATK)
"""

from typing import List, Optional
from ...cards.models import Card
from ...cards.card_type import CardType
from ..result import FusionResult
from .base_strategy import FusionStrategy


class ElementalFusionStrategy(FusionStrategy):
    """
    Elemental Archetype Pairwise Fusion Strategy.
    """

    @property
    def name(self) -> str:
        return "ElementalFusion"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        dragons = [c for c in hand if c.card_type == CardType.DRAGON]
        plants = [c for c in hand if c.card_type == CardType.PLANT]
        if dragons and plants:
            return FusionResult(
                sequence=[dragons[0].index, plants[0].index],
                play_name="Black Forest Dragon",
                estimated_atk=2100,
            )

        beasts = [c for c in hand if c.card_type == CardType.BEAST]
        pyros = [c for c in hand if c.card_type == CardType.PYRO]
        if beasts and pyros:
            return FusionResult(
                sequence=[beasts[0].index, pyros[0].index],
                play_name="Flame Cerebrus",
                estimated_atk=2100,
            )

        rocks = [c for c in hand if c.card_type == CardType.ROCK]
        females = [c for c in hand if c.card_type == CardType.FEMALE]
        if rocks and females:
            return FusionResult(
                sequence=[rocks[0].index, females[0].index],
                play_name="Mystical Sand",
                estimated_atk=2100,
            )

        return None
