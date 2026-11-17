"""
Yu-Gi-Oh! Forbidden Memories - Card Types and Archetypes.

Domain Entity: CardType
Defines the distinct card archetypes recognized in Yu-Gi-Oh! Forbidden Memories
and provides domain queries (e.g. is_monster, is_equip, is_spell).
"""

from enum import Enum
from typing import Set


class CardType(str, Enum):
    """
    Enumeration of classic Yu-Gi-Oh! Forbidden Memories card types.
    Inherits from str so that comparisons with legacy string constants remain valid.
    """
    DRAGON = "Dragon"
    THUNDER = "Thunder"
    SPELLCASTER = "Spellcaster"
    AQUA = "Aqua"
    SEA_SERPENT = "Sea Serpent"
    PYRO = "Pyro"
    BEAST = "Beast"
    PLANT = "Plant"
    ROCK = "Rock"
    FEMALE = "Female"
    WARRIOR = "Warrior"
    ZOMBIE = "Zombie"
    MACHINE = "Machine"
    FIEND = "Fiend"
    EQUIP = "Equip"
    SPELL = "Spell"
    TRAP = "Trap"
    MONSTER = "Monster"
    UNKNOWN = "Unknown"

    @property
    def is_monster(self) -> bool:
        """
        Determines if this card type represents a playable monster creature.
        In Forbidden Memories, all types except Equip, Spell, Trap, and Unknown are monsters.
        """
        non_monster_types: Set["CardType"] = {
            CardType.EQUIP,
            CardType.SPELL,
            CardType.TRAP,
            CardType.UNKNOWN,
        }
        return self not in non_monster_types

    @property
    def is_equip(self) -> bool:
        """Determines if this card type is an equip magic/item."""
        return self == CardType.EQUIP

    @property
    def is_spell(self) -> bool:
        """Determines if this card type is a spell/magic card."""
        return self == CardType.SPELL

    @classmethod
    def from_str(cls, value: str) -> "CardType":
        """
        Case-insensitively parses a string into a CardType.
        Falls back to CardType.UNKNOWN if no match is found.
        """
        if not value:
            return cls.UNKNOWN
        clean = value.strip().lower()
        for member in cls:
            if member.value.lower() == clean or member.name.lower() == clean:
                return member
        return cls.UNKNOWN


# Backward-compatible constant aliases
TYPE_DRAGON = CardType.DRAGON.value
TYPE_THUNDER = CardType.THUNDER.value
TYPE_SPELLCASTER = CardType.SPELLCASTER.value
TYPE_AQUA = CardType.AQUA.value
TYPE_SEA_SERPENT = CardType.SEA_SERPENT.value
TYPE_PYRO = CardType.PYRO.value
TYPE_BEAST = CardType.BEAST.value
TYPE_PLANT = CardType.PLANT.value
TYPE_ROCK = CardType.ROCK.value
TYPE_FEMALE = CardType.FEMALE.value
TYPE_WARRIOR = CardType.WARRIOR.value
TYPE_ZOMBIE = CardType.ZOMBIE.value
TYPE_MACHINE = CardType.MACHINE.value
TYPE_FIEND = CardType.FIEND.value
TYPE_EQUIP = CardType.EQUIP.value
TYPE_SPELL = CardType.SPELL.value
