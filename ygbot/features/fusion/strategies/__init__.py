"""
Fusion Strategies Package.

Separation of Concerns:
Each strategy resides in its own isolated file, obeying the Open/Closed Principle (OCP)
and Single Responsibility Principle (SRP).
"""

from .base_strategy import FusionStrategy
from .meteor_black_dragon import MeteorBlackDragonStrategy
from .thtd_strategy import THTDFusionStrategy
from .discard_cycle_strategy import DiscardAndCycleStrategy
from .equip_buff_strategy import EquipBuffStrategy
from .elemental_fusion_strategy import ElementalFusionStrategy
from .highest_atk_strategy import HighestAtkStrategy

__all__ = [
    "FusionStrategy",
    "MeteorBlackDragonStrategy",
    "THTDFusionStrategy",
    "DiscardAndCycleStrategy",
    "EquipBuffStrategy",
    "ElementalFusionStrategy",
    "HighestAtkStrategy",
]
