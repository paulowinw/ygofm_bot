"""
Twin-Headed Thunder Dragon (THTD) Fusion Strategy.

Artifact: Concrete Strategy
Priority: 2 (Primary workhorse summon in Forbidden Memories)
Recipe: Thunder (CardType.THUNDER) + Dragon (CardType.DRAGON) = Twin-Headed Thunder Dragon (2800 ATK).
Chains extra dragons in hand to boost ATK, plus compatible equips (Dragon Treasure, Shine Palace, Electro-Whip).
Preferred Guardian Star: Pluto.
"""

from typing import List, Optional, Set
from ...cards.models import Card, EquipCard
from ...cards.card_type import CardType
from ..result import FusionResult
from .base_strategy import FusionStrategy


class THTDFusionStrategy(FusionStrategy):
    """
    Twin-Headed Thunder Dragon (2800+ ATK) Strategy.
    """

    @property
    def name(self) -> str:
        return "THTD"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        thunders = [c for c in hand if c.card_type == CardType.THUNDER]
        dragons = [c for c in hand if c.card_type == CardType.DRAGON]

        if not (thunders and dragons):
            return None

        best_thunder = max(thunders, key=lambda t: getattr(t, 'atk', 0))
        best_dragon = max(dragons, key=lambda d: getattr(d, 'atk', 0))

        sequence: List[int] = [best_thunder.index, best_dragon.index]
        used_indices: Set[int] = {best_thunder.index, best_dragon.index}

        for d in dragons:
            if d.index not in used_indices:
                sequence.append(d.index)
                used_indices.add(d.index)

        equips = [c for c in hand if (isinstance(c, EquipCard) or c.is_equip) and c.index not in used_indices]
        compatible_equips = [
            eq for eq in equips
            if not isinstance(eq, EquipCard) or any(t.lower() in ("thunder", "dragon", "light", "sea serpent") for t in eq.target_types) or not eq.target_types
        ]
        for eq in compatible_equips:
            sequence.append(eq.index)
            used_indices.add(eq.index)

        estimated_atk = 2800 + len(compatible_equips) * 500

        return FusionResult(
            sequence=sequence,
            play_name="Twin-Headed Thunder Dragon",
            estimated_atk=estimated_atk,
            guardian_star="Pluto",
        )
