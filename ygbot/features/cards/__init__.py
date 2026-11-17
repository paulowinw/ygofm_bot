"""
Cards Feature Module.
Provides card domain models, catalog, registry factory, and card manager.
"""

from .card_type import (
    CardType,
    TYPE_DRAGON,
    TYPE_THUNDER,
    TYPE_SPELLCASTER,
    TYPE_AQUA,
    TYPE_SEA_SERPENT,
    TYPE_PYRO,
    TYPE_BEAST,
    TYPE_PLANT,
    TYPE_ROCK,
    TYPE_FEMALE,
    TYPE_WARRIOR,
    TYPE_ZOMBIE,
    TYPE_MACHINE,
    TYPE_FIEND,
    TYPE_EQUIP,
    TYPE_SPELL,
)
from .known_cards import KNOWN_CARDS
from .models import Card, MonsterCard, EquipCard, SpellCard
from .registry import CardRegistry
from .card_manager import CardManager

__all__ = [
    "CardType",
    "TYPE_DRAGON",
    "TYPE_THUNDER",
    "TYPE_SPELLCASTER",
    "TYPE_AQUA",
    "TYPE_SEA_SERPENT",
    "TYPE_PYRO",
    "TYPE_BEAST",
    "TYPE_PLANT",
    "TYPE_ROCK",
    "TYPE_FEMALE",
    "TYPE_WARRIOR",
    "TYPE_ZOMBIE",
    "TYPE_MACHINE",
    "TYPE_FIEND",
    "TYPE_EQUIP",
    "TYPE_SPELL",
    "KNOWN_CARDS",
    "Card",
    "MonsterCard",
    "EquipCard",
    "SpellCard",
    "CardRegistry",
    "CardManager",
]
