"""
Cards package for YGBot.

Contains domain representations for Yu-Gi-Oh! Forbidden Memories cards,
card types, archetype rules, and the CardRegistry factory.
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
from .models import Card, MonsterCard, EquipCard, SpellCard
from .registry import CardRegistry, KNOWN_CARDS

__all__ = [
    "CardType",
    "Card",
    "MonsterCard",
    "EquipCard",
    "SpellCard",
    "CardRegistry",
    "KNOWN_CARDS",
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
]
