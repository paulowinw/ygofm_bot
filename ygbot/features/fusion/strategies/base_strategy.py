"""
Base Fusion Strategy Interface.

Design Pattern: Strategy Pattern (Component: Strategy Interface)
Defines the contract for hand evaluation.
"""

from abc import ABC, abstractmethod
from typing import List, Optional
from ...cards.models import Card
from ..result import FusionResult


class FusionStrategy(ABC):
    """
    Abstract Strategy defining the contract for analyzing a hand of cards
    and determining an optimal play sequence.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """Identifier name of the strategy."""
        pass

    @abstractmethod
    def evaluate(self, hand: List[Card]) -> Optional[FusionResult]:
        """
        Evaluates the cards currently in hand.
        
        Args:
            hand: List of typed Card domain objects with their slot indices assigned.
            
        Returns:
            FusionResult if this strategy successfully identified a valid play,
            or None if the hand does not satisfy this strategy's requirements.
        """
        pass
