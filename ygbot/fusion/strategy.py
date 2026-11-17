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


class MeteorBlackDragonStrategy(FusionStrategy):
    """
    Meteor Black Dragon (3500+ ATK) Fusion Strategy.
    
    Highest-priority summon as demonstrated in the duel video.
    Recipe: Red-Eyes B. Dragon (2400 ATK) + Meteor Dragon (1800 ATK) = Meteor Black Dragon (3500 ATK).
    Then checks for compatible Equip cards (e.g. Dragon Treasure) to add to the fusion (+500 ATK each).
    Preferred Guardian Star: Sun (beats Moon, +500 ATK against dark/spellcasters).
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

        # Sequence as shown in the video: Red-Eyes first, Meteor Dragon second
        sequence: List[int] = [re_dragon.index, m_dragon.index]
        used_indices: Set[int] = {re_dragon.index, m_dragon.index}

        # Check for compatible equip cards to add to the fusion
        equips = [c for c in hand if (isinstance(c, EquipCard) or c.is_equip) and c.index not in used_indices]
        compatible_equips = [
            eq for eq in equips
            if not isinstance(eq, EquipCard) or eq.can_equip_to(re_dragon) or not eq.target_types or any(t.lower() == "dragon" for t in eq.target_types)
        ]
        for eq in compatible_equips:
            sequence.append(eq.index)
            used_indices.add(eq.index)

        # Base 3500 ATK + 500 per equip card added
        estimated_atk = 3500 + len(compatible_equips) * 500

        return FusionResult(
            sequence=sequence,
            play_name="Meteor Black Dragon",
            estimated_atk=estimated_atk,
            guardian_star="Sun",
        )


class THTDFusionStrategy(FusionStrategy):
    """
    Twin-Headed Thunder Dragon (2800+ ATK) Strategy.
    
    Recipe: Thunder (CardType.THUNDER) + Dragon (CardType.DRAGON) = Twin-Headed Thunder Dragon (2800 ATK).
    After that, checks for compatible Equip cards to add to the fusion.
    Preferred Guardian Star: Pluto (beats Neptune, +500 ATK).
    """

    @property
    def name(self) -> str:
        return "THTD"

    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        thunders = [c for c in hand if c.card_type == CardType.THUNDER]
        dragons = [c for c in hand if c.card_type == CardType.DRAGON]

        if not (thunders and dragons):
            return None

        # Choose best thunder and best dragon
        best_thunder = max(thunders, key=lambda t: getattr(t, 'atk', 0))
        best_dragon = max(dragons, key=lambda d: getattr(d, 'atk', 0))

        sequence: List[int] = [best_thunder.index, best_dragon.index]
        used_indices: Set[int] = {best_thunder.index, best_dragon.index}

        # Chain any extra dragons in hand to boost ATK
        for d in dragons:
            if d.index not in used_indices:
                sequence.append(d.index)
                used_indices.add(d.index)

        # Check for compatible equip cards to add to the fusion
        equips = [c for c in hand if (isinstance(c, EquipCard) or c.is_equip) and c.index not in used_indices]
        compatible_equips = [
            eq for eq in equips
            if not isinstance(eq, EquipCard) or any(t.lower() in ("thunder", "dragon", "light", "sea serpent") for t in eq.target_types) or not eq.target_types
        ]
        for eq in compatible_equips:
            sequence.append(eq.index)
            used_indices.add(eq.index)

        # Base 2800 ATK + 500 per equip card added
        estimated_atk = 2800 + len(compatible_equips) * 500

        return FusionResult(
            sequence=sequence,
            play_name="Twin-Headed Thunder Dragon",
            estimated_atk=estimated_atk,
            guardian_star="Pluto",
        )


class DiscardAndCycleStrategy(FusionStrategy):
    """
    Discard and Hand Cycling Strategy.
    
    Applied when neither Meteor Black Dragon nor Twin-Headed Thunder Dragon can be fused.
    Rules:
    1. If there's no fusion card for THTD, discard repeated dragons and repeated thunder monsters.
    2. If there are more than 2 equip cards, discard the extra ones.
    3. Fuses/burns the discarded dead cards into the graveyard, keeping the strongest monster
       on the field, so that the hand draws fresh cards next turn!
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

        # 1. Discard repeated dragons (keep only the single best dragon)
        if len(dragons) > 1:
            dragons_sorted = sorted(dragons, key=lambda d: getattr(d, "atk", 0), reverse=True)
            keeper_monster = dragons_sorted[0]
            cards_to_discard.extend(dragons_sorted[1:])
        elif len(dragons) == 1:
            keeper_monster = dragons[0]

        # 2. Discard repeated thunders (keep only the single best thunder)
        if len(thunders) > 1:
            thunders_sorted = sorted(thunders, key=lambda t: getattr(t, "atk", 0), reverse=True)
            if keeper_monster is None or getattr(thunders_sorted[0], "atk", 0) > getattr(keeper_monster, "atk", 0):
                keeper_monster = thunders_sorted[0]
            cards_to_discard.extend(thunders_sorted[1:])
        elif len(thunders) == 1 and keeper_monster is None:
            keeper_monster = thunders[0]

        # 3. Discard extra equips if there are more than 2 equips
        if len(equips) > 2:
            cards_to_discard.extend(equips[2:])

        # If keeper is still None, pick best other monster if available
        if keeper_monster is None and other_monsters:
            keeper_monster = max(other_monsters, key=lambda m: getattr(m, "atk", 0))

        # If we have dead cards to discard, sequence them
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
