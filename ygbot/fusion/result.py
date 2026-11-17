"""
Result Value Object for Fusion Evaluation.

Encapsulates the decision made by a FusionStrategy, containing:
- sequence: The ordered indices of hand cards to click/play.
- play_name: Name of the resulting monster or fusion play.
- estimated_atk: Calculated total attack points including fusions and equips.

Provides 3-element tuple unpacking for full backward compatibility:
    sequence, play_name, estimated_atk = fusion_result
"""

from dataclasses import dataclass
from typing import List, Iterator, Any, Optional


@dataclass
class FusionResult:
    """
    Result of evaluating a hand of cards with a FusionStrategy.
    """
    sequence: List[int]
    play_name: str
    estimated_atk: int
    guardian_star: Optional[str] = None

    def __iter__(self) -> Iterator[Any]:
        """Allows unpacking: sequence, name, atk = result"""
        yield self.sequence
        yield self.play_name
        yield self.estimated_atk

    def __getitem__(self, item: int) -> Any:
        return (self.sequence, self.play_name, self.estimated_atk)[item]

    def __len__(self) -> int:
        return 3

    def __repr__(self) -> str:
        return f"<FusionResult play='{self.play_name}' atk={self.estimated_atk} sequence={self.sequence}>"
