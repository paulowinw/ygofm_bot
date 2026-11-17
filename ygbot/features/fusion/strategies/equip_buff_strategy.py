"""
Equip and Monster Buff Strategy.

Artifact: Concrete Strategy
Priority: 4 (Monster Equip Buffing)
Selects the best base monster (with weighting for duplicates and compatible equips),
chains all compatible equips, and chains duplicate monsters for fusion buffs.
"""

from typing import List, Optional, Set
from ...cards.models import Card, MonsterCard, EquipCard
from ..result import FusionResult
from .base_strategy import FusionStrategy


class EquipBuffStrategy(FusionStrategy):
    """
    Equip & Monster Buff Strategy.
    """

    @property
    def name(self) -> str:
        return "EquipBuff"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        monsters = [c for c in hand if c.is_monster]
        equips = [c for c in hand if isinstance(c, EquipCard) or c.is_equip]

        if not (monsters and equips):
            return None

        def monster_score(m: Card) -> int:
            base_atk = m.atk if isinstance(m, MonsterCard) else getattr(m, "atk", 1000)
            dup_count = sum(1 for other in monsters if other.name == m.name)
            compatible_equips = sum(
                1 for eq in equips
                if isinstance(eq, EquipCard) and eq.can_equip_to(m)
            )
            return base_atk + (dup_count * 600) + (compatible_equips * 500)

        best_monster = max(monsters, key=monster_score)
        base_atk = best_monster.atk if isinstance(best_monster, MonsterCard) else getattr(best_monster, "atk", 1000)

        sequence: List[int] = [best_monster.index]
        used_indices: Set[int] = {best_monster.index}

        for eq in equips:
            if eq.index not in used_indices:
                sequence.append(eq.index)
                used_indices.add(eq.index)

        for m in monsters:
            if m.index not in used_indices and m.name == best_monster.name:
                sequence.append(m.index)
                used_indices.add(m.index)

        total_atk = base_atk + len(equips) * 500 + (len(sequence) - 1 - len(equips)) * 500
        return FusionResult(
            sequence=sequence,
            play_name=f"{best_monster.name} (Equipped)",
            estimated_atk=total_atk,
        )
