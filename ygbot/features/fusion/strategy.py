"""
Fusion Strategy Facade and Coordinator.

Exports the base FusionStrategy interface and all concrete strategies
from the strategies package.
"""

from .strategies import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)

__all__ = [
    "FusionStrategy",
    "MeteorBlackDragonStrategy",
    "THTDFusionStrategy",
    "DiscardAndCycleStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
]
