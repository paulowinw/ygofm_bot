"""
Fusion package for YGBot.

Contains the FusionEngine (Context in the Strategy Pattern),
the FusionStrategy interface, concrete fusion strategies,
and the FusionResult value object.
"""

from .result import FusionResult
from .strategy import (
    FusionStrategy,
    THTDFusionStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)
from .engine import FusionEngine

__all__ = [
    "FusionResult",
    "FusionStrategy",
    "THTDFusionStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
    "FusionEngine",
]
