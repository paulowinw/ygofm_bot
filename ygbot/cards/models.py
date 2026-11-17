"""
Domain Models for Yu-Gi-Oh! Forbidden Memories Cards.

Separation of Concerns:
Cards are modeled as rich domain objects rather than raw strings or untyped dictionaries.
This allows polymorphically querying card properties (is_monster, can_equip_to, atk)
and decoupling card state from fusion evaluation logic.
"""

from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
from .card_type import CardType


@dataclass
class Card:
    """
    Base Card domain class.
    
    Attributes:
        name: Name of the card.
        card_type: The CardType enum representing this card's archetype.
        index: Zero-based position of this card in the player's 5-card hand (0..4).
    """
    name: str
    card_type: CardType = CardType.UNKNOWN
    index: int = -1

    @property
    def is_monster(self) -> bool:
        """Convenience property delegating to CardType."""
        return self.card_type.is_monster

    @property
    def is_equip(self) -> bool:
        """Convenience property delegating to CardType."""
        return self.card_type.is_equip

    @property
    def is_spell(self) -> bool:
        """Convenience property delegating to CardType."""
        return self.card_type.is_spell

    def to_dict(self) -> Dict[str, Any]:
        """Serializes card to dictionary format for legacy compatibility."""
        return {
            "name": self.name,
            "type": self.card_type.value,
            "index": self.index,
        }

    def __repr__(self) -> str:
        return f"<{self.__class__.__name__} name='{self.name}' type={self.card_type.value} index={self.index}>"


@dataclass
class MonsterCard(Card):
    """
    Represents a summonable combat monster.
    
    Attributes:
        atk: Base attack points.
        def_: Base defense points.
        guardian_star_primary: Primary guardian star.
        guardian_star_secondary: Secondary guardian star.
    """
    atk: int = 1000
    def_: int = 1000
    guardian_star_primary: Optional[str] = None
    guardian_star_secondary: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "atk": self.atk,
            "def": self.def_,
        })
        return data

    def __repr__(self) -> str:
        return (
            f"<MonsterCard name='{self.name}' type={self.card_type.value} "
            f"atk={self.atk} def={self.def_} index={self.index}>"
        )


@dataclass
class EquipCard(Card):
    """
    Represents an equip magic card that buffs compatible monsters.
    
    Attributes:
        buff: Attack/Defense stat increase (typically +500 in PS1 / FM Online).
        target_types: Archetypes/attributes eligible for this buff (e.g. ['Dragon', 'Thunder']).
    """
    card_type: CardType = CardType.EQUIP
    buff: int = 500
    target_types: List[str] = field(default_factory=list)

    def can_equip_to(self, monster: Card) -> bool:
        """
        Determines if this equip card can be applied to the target monster.
        Checks target_types case-insensitively against the monster's archetype.
        """
        if not monster.is_monster:
            return False
        if not self.target_types:
            return True  # Universal equip
        m_type = monster.card_type.value.lower()
        return any(t.lower() == m_type for t in self.target_types)

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "buff": self.buff,
            "target": list(self.target_types),
        })
        return data

    def __repr__(self) -> str:
        return (
            f"<EquipCard name='{self.name}' buff=+{self.buff} "
            f"targets={self.target_types} index={self.index}>"
        )


@dataclass
class SpellCard(Card):
    """
    Represents a non-equip magic or spell card (e.g. Raigeki, Dark Hole).
    
    Attributes:
        atk: Priority ranking value (set high so spells are prioritized if used in combat).
        effect: Brief description of the card's effect.
    """
    card_type: CardType = CardType.SPELL
    atk: int = 9999
    effect: str = "destroy"

    def to_dict(self) -> Dict[str, Any]:
        data = super().to_dict()
        data.update({
            "atk": self.atk,
            "effect": self.effect,
        })
        return data

    def __repr__(self) -> str:
        return f"<SpellCard name='{self.name}' effect='{self.effect}' index={self.index}>"
