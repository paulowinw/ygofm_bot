"""
Card Manager for Yu-Gi-Oh! Forbidden Memories.

Artifact: Card Manager
Responsibilities:
- Reads, evaluates, and locates card entities on the game board / hand.
- Converts raw card representations (DOM strings, images, hashes) into typed Card domain models.
- Tracks player hand composition and field state.
"""

from typing import List, Optional, Dict, Any
from .models import Card
from .registry import CardRegistry


class CardManager:
    """Manages reading, evaluating, and locating cards on screen and in memory."""

    def __init__(self, registry: Optional[CardRegistry] = None):
        self.registry = registry or CardRegistry.get_instance()
        self.current_hand: List[Card] = []

    def parse_hand(self, raw_cards: List[Any]) -> List[Card]:
        """
        Converts a list of raw card names, dicts, or objects into typed Card domain models
        with assigned slot indices (0..4).
        """
        cards: List[Card] = []
        for idx, item in enumerate(raw_cards[:5]):
            card = self.registry.from_any(item, index=idx)
            cards.append(card)
        self.current_hand = cards
        return cards

    def get_card_at_slot(self, slot_index: int) -> Optional[Card]:
        """Returns the card domain object at the given hand slot."""
        if 0 <= slot_index < len(self.current_hand):
            return self.current_hand[slot_index]
        return None

    def evaluate_hand_stats(self) -> Dict[str, Any]:
        """Computes summary statistics for cards currently in hand."""
        monsters = [c for c in self.current_hand if c.is_monster]
        equips = [c for c in self.current_hand if c.is_equip]
        spells = [c for c in self.current_hand if c.is_spell]
        
        max_atk = max((getattr(m, "atk", 0) for m in monsters), default=0)
        return {
            "total": len(self.current_hand),
            "monsters": len(monsters),
            "equips": len(equips),
            "spells": len(spells),
            "max_atk": max_atk,
        }
