"""
Meteor Black Dragon Fusion Strategy.

Artifact: Concrete Strategy
Priority: 1 (Highest base attack summon in Forbidden Memories speedruns)
Recipe: Red-Eyes B. Dragon (2400 ATK) + Meteor Dragon (1800 ATK) = Meteor Black Dragon (3500 ATK).
Chains compatible equip spells (Dragon Treasure) to reach 4000+ ATK.
Preferred Guardian Star: Sun.
"""

from typing import List, Optional, Set
from ...cards.models import Card, EquipCard
from ..result import FusionResult
from .base_strategy import FusionStrategy


class MeteorBlackDragonStrategy(FusionStrategy):
    """
    Meteor Black Dragon (3500+ ATK) Strategy.
    """

    @property
    def name(self) -> str:
        return "MeteorBlackDragon"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        meteor_dragons = [
            c for c in hand
            if "meteor dragon" in c.name.lower() and "meteor black dragon" not in c.name.lower()
        ]
        red_eyes = [
            c for c in hand
            if "red-eyes" in c.name.lower() or "red eyes" in c.name.lower()
        ]

        if not (meteor_dragons and red_eyes):
            return None

        m_dragon = meteor_dragons[0]
        re_dragon = red_eyes[0]

        sequence: List[int] = [re_dragon.index, m_dragon.index]
        used_indices: Set[int] = {re_dragon.index, m_dragon.index}

        equips = [c for c in hand if (isinstance(c, EquipCard) or c.is_equip) and c.index not in used_indices]
        compatible_equips = [
            eq for eq in equips
            if not isinstance(eq, EquipCard) or eq.can_equip_to(re_dragon) or not eq.target_types or any(t.lower() == "dragon" for t in eq.target_types)
        ]
        for eq in compatible_equips:
            sequence.append(eq.index)
            used_indices.add(eq.index)

        estimated_atk = 3500 + len(compatible_equips) * 500

        return FusionResult(
            sequence=sequence,
            play_name="Meteor Black Dragon",
            estimated_atk=estimated_atk,
            guardian_star="Sun",
        )
