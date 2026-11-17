"""
Fusion Feature Package.
Provides fusion strategies and result value objects.
Note: The main fusion engine logic resides in ygbot.actions.game_board.fusion_action.
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

__all__ = [
    "FusionResult",
    "FusionStrategy",
    "MeteorBlackDragonStrategy",
    "THTDFusionStrategy",
    "DiscardAndCycleStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
]
