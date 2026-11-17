"""
Fusion package for YGBot.

Contains the FusionEngine (Context in the Strategy Pattern),
the FusionStrategy interface, concrete fusion strategies,
and the FusionResult value object.
"""

from .result import FusionResult
from .strategy import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)
from .engine import FusionEngine

__all__ = [
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
