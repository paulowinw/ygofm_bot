"""
Highest Attack Standalone Fallback Strategy.

Artifact: Concrete Strategy
Priority: 6 (Fallback)
Selects the monster card with the highest base ATK from hand when
no viable fusion recipes are found.
"""

from typing import List, Optional
from ...cards.models import Card, MonsterCard
from ..result import FusionResult
from .base_strategy import FusionStrategy


class HighestAtkStrategy(FusionStrategy):
    """
    Fallback / Standalone Strategy.
    """

    @property
    def name(self) -> str:
        return "HighestAtk"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        monsters = [c for c in hand if c.is_monster]
        if monsters:
            best_monster = max(
                monsters,
                key=lambda m: m.atk if isinstance(m, MonsterCard) else getattr(m, "atk", 1000),
            )
            atk = best_monster.atk if isinstance(best_monster, MonsterCard) else getattr(best_monster, "atk", 1000)
            return FusionResult(
                sequence=[best_monster.index],
                play_name=best_monster.name,
                estimated_atk=atk,
            )

        if hand:
            first_card = hand[0]
            atk = getattr(first_card, "atk", 1000)
            return FusionResult(
                sequence=[first_card.index if first_card.index >= 0 else 0],
                play_name=first_card.name,
                estimated_atk=atk,
            )

        return None
