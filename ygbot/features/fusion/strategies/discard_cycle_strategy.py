"""
Discard and Cycle Strategy.

Artifact: Concrete Strategy
Priority: 3 (Hand Cycling / Resource Management)
Applied when neither Meteor Black Dragon nor Twin-Headed Thunder Dragon can be fused.
Rules:
1. Discard duplicate dragons (keep best dragon).
2. Discard duplicate thunders (keep best thunder).
3. Discard extra equips if there are > 2 equips in hand.
4. Fuses/burns the dead cards to cycle into fresh draws next turn.
"""

from typing import List, Optional
from ...cards.models import Card, EquipCard
from ...cards.card_type import CardType
from ..result import FusionResult
from .base_strategy import FusionStrategy


class DiscardAndCycleStrategy(FusionStrategy):
    """
    Discard and Hand Cycling Strategy.
    """

    @property
    def name(self) -> str:
        return "DiscardAndCycle"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        dragons = [c for c in hand if c.card_type == CardType.DRAGON]
        thunders = [c for c in hand if c.card_type == CardType.THUNDER]
        equips = [c for c in hand if isinstance(c, EquipCard) or c.is_equip]
        other_monsters = [
            c for c in hand
            if c.is_monster and c.card_type not in (CardType.DRAGON, CardType.THUNDER)
        ]

        cards_to_discard: List[Card] = []
        keeper_monster: Optional[Card] = None

        if len(dragons) > 1:
            dragons_sorted = sorted(dragons, key=lambda d: getattr(d, "atk", 0), reverse=True)
            keeper_monster = dragons_sorted[0]
            cards_to_discard.extend(dragons_sorted[1:])
        elif len(dragons) == 1:
            keeper_monster = dragons[0]

        if len(thunders) > 1:
            thunders_sorted = sorted(thunders, key=lambda t: getattr(t, "atk", 0), reverse=True)
            if keeper_monster is None or getattr(thunders_sorted[0], "atk", 0) > getattr(keeper_monster, "atk", 0):
                keeper_monster = thunders_sorted[0]
            cards_to_discard.extend(thunders_sorted[1:])
        elif len(thunders) == 1 and keeper_monster is None:
            keeper_monster = thunders[0]

        if len(equips) > 2:
            cards_to_discard.extend(equips[2:])

        if keeper_monster is None and other_monsters:
            keeper_monster = max(other_monsters, key=lambda m: getattr(m, "atk", 0))

        if cards_to_discard:
            sequence = [c.index for c in cards_to_discard]
            if keeper_monster and keeper_monster.index not in sequence:
                sequence.append(keeper_monster.index)
                play_name = f"Discard ({len(cards_to_discard)} dead cards) -> {keeper_monster.name}"
                atk = getattr(keeper_monster, "atk", 1000)
                star = getattr(keeper_monster, "guardian_star_primary", None) or "Pluto"
            else:
                play_name = f"Discard ({len(cards_to_discard)} dead cards)"
                atk = 0
                star = "Pluto"

            return FusionResult(
                sequence=sequence,
                play_name=play_name,
                estimated_atk=atk,
                guardian_star=star,
            )

        return None
