"""
Fusion Strategy Pattern Implementations for Yu-Gi-Oh! Forbidden Memories.

Design Pattern: Strategy Pattern
- Strategy Interface: FusionStrategy
- Concrete Strategies:
    * THTDFusionStrategy: Prioritizes the Twin-Headed Thunder Dragon (2800 ATK) meta strategy.
    * EquipBuffStrategy: Matches monsters with applicable Equip cards and duplicates.
    * ElementalFusionStrategy: Identifies classic secondary recipes (Dragon+Plant, Beast+Pyro, Rock+Female).
    * HighestAtkStrategy: Fallback that plays the monster with highest standalone base ATK.

Interaction between Cards, CardTypes, and Strategies:
Strategies receive a list of rich `Card` domain models. Rather than parsing raw string
keys or nested dictionaries, strategies query domain properties (e.g. `card.card_type`,
`card.is_monster`, `equip.can_equip_to(monster)`) to determine valid fusion paths.
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Set
from ..cards import Card, MonsterCard, EquipCard, CardType
from .result import FusionResult


class FusionStrategy(ABC):
    """
    Abstract Strategy defining the contract for analyzing a hand of cards
    and determining an optimal play sequence.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the strategy."""
        pass

    @abstractmethod
    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        """
        Evaluates the cards currently in hand.
        
        Args:
            hand: List of typed Card domain objects with their slot indices assigned.
            
        Returns:
            FusionResult if this strategy successfully identified a valid play,
            or None if the hand does not satisfy this strategy's requirements.
        """
        pass


class THTDFusionStrategy(FusionStrategy):
    """
    Twin-Headed Thunder Dragon (THTD) Strategy.
    
    The cornerstone speedrun/farming strategy in Yu-Gi-Oh! Forbidden Memories.
    Recipe: Dragon (CardType.DRAGON) + Thunder (CardType.THUNDER) = 2800 ATK.
    Also chains any additional dragons or equips in hand to maximize damage.
    """

    @property
    def name(self) -> str:
        return "THTD"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        thunders = [c for c in hand if c.card_type == CardType.THUNDER]
        dragons = [c for c in hand if c.card_type == CardType.DRAGON]
        equips = [c for c in hand if isinstance(c, EquipCard) or c.is_equip]

        if not (thunders and dragons):
            return None

        first_thunder = thunders[0]
        first_dragon = dragons[0]

        sequence: List[int] = [first_thunder.index, first_dragon.index]
        used_indices: Set[int] = {first_thunder.index, first_dragon.index}

        # Chain any extra dragons in hand to boost ATK
        for d in dragons[1:]:
            if d.index not in used_indices:
                sequence.append(d.index)
                used_indices.add(d.index)

        # Chain compatible equips to further boost ATK
        for eq in equips:
            if eq.index not in used_indices:
                sequence.append(eq.index)
                used_indices.add(eq.index)

        # Twin-Headed Thunder Dragon base ATK: 2800 + 500 per additional chained card
        estimated_atk = 2800 + (len(sequence) - 2) * 500
        return FusionResult(
            sequence=sequence,
            play_name="Twin-Headed Thunder Dragon",
            estimated_atk=estimated_atk,
        )


class EquipBuffStrategy(FusionStrategy):
    """
    Equip & Monster Buff Strategy.
    
    Applies when the hand contains one or more Equip cards and monsters.
    Selects the best base monster (giving bonus weight to duplicates and equips),
    chains all compatible equips, and chains duplicate monsters for fusion buffs.
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
            # Duplicate monster cards can fuse into stronger forms (+600 bonus)
            dup_count = sum(1 for other in monsters if other.name == m.name)
            # Bonus if equips specifically target this monster's type
            compatible_equips = sum(
                1 for eq in equips
                if isinstance(eq, EquipCard) and eq.can_equip_to(m)
            )
            return base_atk + (dup_count * 600) + (compatible_equips * 500)

        best_monster = max(monsters, key=monster_score)
        base_atk = best_monster.atk if isinstance(best_monster, MonsterCard) else getattr(best_monster, "atk", 1000)

        sequence: List[int] = [best_monster.index]
        used_indices: Set[int] = {best_monster.index}

        # Chain equips
        for eq in equips:
            if eq.index not in used_indices:
                sequence.append(eq.index)
                used_indices.add(eq.index)

        # Chain duplicate monsters
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


class ElementalFusionStrategy(FusionStrategy):
    """
    Elemental Archetype Pairwise Fusion Strategy.
    
    Handles classic secondary high-tier fusions in Forbidden Memories:
    - Dragon + Plant -> Black Forest Dragon (2100 ATK)
    - Beast + Pyro -> Flame Cerebrus (2100 ATK)
    - Rock + Female -> Mystical Sand (2100 ATK)
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


class HighestAtkStrategy(FusionStrategy):
    """
    Fallback / Standalone Strategy.
    
    Selects the monster card with the highest base ATK from hand when
    no viable fusion recipes are found.
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
