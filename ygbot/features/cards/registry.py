"""
Card Registry and Factory for Yu-Gi-Oh! Forbidden Memories.

Design Patterns Applied:
1. Registry Pattern: Central repository of known card archetypes, stats, and equip affinities.
2. Factory Method Pattern: Constructs specialized domain models (MonsterCard, EquipCard, SpellCard)
   from either database definitions, arbitrary dictionaries, or heuristic string matching.
"""

from typing import Dict, Any, Optional, Union
from .card_type import CardType
from .known_cards import KNOWN_CARDS
from .models import Card, MonsterCard, EquipCard, SpellCard


class CardRegistry:
    """
    Factory & Registry for cards.
    Maintains known card data and creates polymorphically typed Card instances.
    """
    _instance: Optional["CardRegistry"] = None

    def __init__(self, card_db: Optional[Dict[str, Dict[str, Any]]] = None):
        self._db: Dict[str, Dict[str, Any]] = card_db if card_db is not None else KNOWN_CARDS

    @classmethod
    def get_instance(cls) -> "CardRegistry":
        """Singleton accessor for default registry."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def create_card_from_name(self, card_name: str, index: int = -1) -> Card:
        """
        Factory method: Creates a typed Card domain object by looking up known cards
        or falling back to heuristic keyword extraction.
        """
        clean_name = card_name.strip()
        
        # 1. Exact match in database
        if clean_name in self._db:
            raw = self._db[clean_name]
            ctype = CardType.from_str(raw.get("type", ""))
            if ctype.is_equip:
                return EquipCard(
                    name=clean_name,
                    card_type=ctype,
                    index=index,
                    buff=raw.get("buff", 500),
                    target_types=raw.get("target", []),
                )
            elif ctype.is_spell:
                return SpellCard(
                    name=clean_name,
                    card_type=ctype,
                    index=index,
                    atk=raw.get("atk", 9999),
                )
            else:
                return MonsterCard(
                    name=clean_name,
                    card_type=ctype,
                    index=index,
                    atk=raw.get("atk", 1000),
                    def_=raw.get("def", 1000),
                )

        # 2. Heuristic extraction for unknown cards (OCR or web text)
        return self._create_card_by_heuristics(clean_name, index)

    def _create_card_by_heuristics(self, name: str, index: int = -1) -> Card:
        """Infers card type and stats from name tokens."""
        lower = name.lower()
        if any(w in lower for w in ["equip", "palace", "treasure", "energy", "fangs", "whip"]):
            return EquipCard(
                name=name,
                card_type=CardType.EQUIP,
                index=index,
                buff=500,
                target_types=[],
            )
        if any(w in lower for w in ["spell", "hole", "duster", "raigeki"]):
            return SpellCard(
                name=name,
                card_type=CardType.SPELL,
                index=index,
                atk=9999,
            )

        # Infer monster archetype
        ctype = CardType.MONSTER
        atk = 1000
        if any(w in lower for w in ["dragon", "drg"]):
            ctype = CardType.DRAGON
            atk = 1500
        elif any(w in lower for w in ["thunder", "bolt", "electric", "kaminari"]):
            ctype = CardType.THUNDER
            atk = 1500
        elif any(w in lower for w in ["plant", "flower", "tree"]):
            ctype = CardType.PLANT
        elif any(w in lower for w in ["flame", "fire", "pyro"]):
            ctype = CardType.PYRO
        elif any(w in lower for w in ["beast", "wolf", "fang"]):
            ctype = CardType.BEAST
        elif any(w in lower for w in ["rock", "stone"]):
            ctype = CardType.ROCK

        return MonsterCard(
            name=name,
            card_type=ctype,
            index=index,
            atk=atk,
            def_=1000,
        )

    def from_any(self, item: Union[str, Dict[str, Any], Card], index: int = -1) -> Card:
        """
        Universal adapter: Converts a string, dictionary, or Card into a typed Card object.
        """
        if isinstance(item, Card):
            if index >= 0:
                item.index = index
            return item
        
        if isinstance(item, str):
            return self.create_card_from_name(item, index=index)
        
        if isinstance(item, dict):
            name = item.get("name", f"Card {index+1}")
            type_str = item.get("type")
            ctype = CardType.from_str(type_str) if type_str else None
            
            # If type was missing from dict, infer from name
            if not ctype or ctype == CardType.UNKNOWN:
                inferred = self.create_card_from_name(name, index=index)
                if "atk" in item and isinstance(inferred, MonsterCard):
                    inferred.atk = item["atk"]
                if "def" in item and isinstance(inferred, MonsterCard):
                    inferred.def_ = item["def"]
                return inferred
            
            if ctype.is_equip:
                return EquipCard(
                    name=name,
                    card_type=ctype,
                    index=index,
                    buff=item.get("buff", 500),
                    target_types=item.get("target", item.get("target_types", [])),
                )
            elif ctype.is_spell:
                return SpellCard(
                    name=name,
                    card_type=ctype,
                    index=index,
                    atk=item.get("atk", 9999),
                    effect=item.get("effect", "destroy"),
                )
            else:
                return MonsterCard(
                    name=name,
                    card_type=ctype,
                    index=index,
                    atk=item.get("atk", 1000),
                    def_=item.get("def", 1000),
                )

        return MonsterCard(name=f"Card {index+1}", card_type=CardType.UNKNOWN, index=index)
