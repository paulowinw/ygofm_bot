"""
Fusion Feature Package.
Provides fusion engine, strategies, and result value objects.
"""

from .result import FusionResult
from .engine import FusionEngine
from .strategy import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)

__all__ = [
    "FusionResult",
    "FusionEngine",
    "FusionStrategy",
    "MeteorBlackDragonStrategy",
    "THTDFusionStrategy",
    "DiscardAndCycleStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
]
