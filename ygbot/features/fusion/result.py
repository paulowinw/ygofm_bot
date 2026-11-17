"""
Fusion Result Value Object.

Encapsulates outcome of a fusion calculation:
- sequence: Hand slot indices to be played/fused
- play_name: Name of resulting card or tactical play
- estimated_atk: Attack power of resulting card
- guardian_star: Recommended Guardian Star (e.g. Pluto, Sun)
"""

from dataclasses import dataclass
from typing import List, Optional


@dataclass(frozen=True)
class FusionResult:
    """
    Value object representing the evaluated play from a hand of cards.
    Supports 3-element tuple unpacking for legacy compatibility:
    `sequence, play_name, atk = result`
    """
    sequence: List[int]
    play_name: str
    estimated_atk: int
    guardian_star: Optional[str] = None

    def __iter__(self):
        """Allows unpacking as (sequence, play_name, estimated_atk)."""
        yield self.sequence
        yield self.play_name
        yield self.estimated_atk

    def __getitem__(self, index: int):
        """Allows index-based tuple access (e.g. result[0])."""
        return (self.sequence, self.play_name, self.estimated_atk)[index]

    def __len__(self) -> int:
        return 3
