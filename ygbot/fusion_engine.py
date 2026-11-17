"""
Yu-Gi-Oh! Forbidden Memories Fusion Solver and Card Database.

Note:
This module serves as a backward-compatibility facade for the refactored architecture.
The codebase has been reorganized into dedicated domain packages:
  - ygbot.cards: CardType, Card, MonsterCard, EquipCard, SpellCard, CardRegistry
  - ygbot.fusion: FusionEngine, FusionResult, FusionStrategy, and concrete strategies

All legacy constants, dictionaries, and classes are re-exported below.
"""

# Re-export card types and legacy constants
from .cards.card_type import (
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

# Re-export card models and database
from .cards.models import (
    Card,
    MonsterCard,
    EquipCard,
    SpellCard,
)
from .cards.registry import (
    CardRegistry,
    KNOWN_CARDS,
)

# Re-export fusion strategies and engine
from .fusion.result import FusionResult
from .fusion.strategy import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)
from .fusion.engine import FusionEngine

__all__ = [
    # Card Types
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
    # Cards
    "Card",
    "MonsterCard",
    "EquipCard",
    "SpellCard",
    "CardRegistry",
    "KNOWN_CARDS",
    # Fusion
    "FusionResult",
    "FusionStrategy",
    "MeteorBlackDragonStrategy",
    "THTDFusionStrategy",
    "DiscardAndCycleStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
    "FusionEngine",
]
