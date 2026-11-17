"""
Card Registry and Factory for Yu-Gi-Oh! Forbidden Memories.

Design Patterns Applied:
1. Registry Pattern: Central repository of known card archetypes, stats, and equip affinities.
2. Factory Method Pattern: Constructs specialized domain models (MonsterCard, EquipCard, SpellCard)
   from either database definitions, arbitrary dictionaries, or heuristic string matching.
"""

from typing import Dict, Any, Optional, Union
from .card_type import (
    CardType,
    TYPE_DRAGON,
    TYPE_THUNDER,
    TYPE_SPELLCASTER,
    TYPE_AQUA,
    TYPE_SEA_SERPENT,
    TYPE_PYRO,
    TYPE_BEAST,
    TYPE_PLANT,
    TYPE_ROCK,
    TYPE_FEMALE,
    TYPE_WARRIOR,
    TYPE_ZOMBIE,
    TYPE_MACHINE,
    TYPE_FIEND,
    TYPE_EQUIP,
    TYPE_SPELL,
)
from .models import Card, MonsterCard, EquipCard, SpellCard


# Database of well-known Forbidden Memories cards, stats, and types
KNOWN_CARDS: Dict[str, Dict[str, Any]] = {
    # Thunders
    "Bolt Escargot": {"type": TYPE_THUNDER, "atk": 1400, "def": 1500},
    "Kaminari Attack": {"type": TYPE_THUNDER, "atk": 1900, "def": 1400},
    "Mega Thunderball": {"type": TYPE_THUNDER, "atk": 750, "def": 600},
    "Electric Lizard": {"type": TYPE_THUNDER, "atk": 850, "def": 800},
    "Lala Li-Oon": {"type": TYPE_THUNDER, "atk": 600, "def": 600},
    "Thunder Dragon": {"type": TYPE_THUNDER, "atk": 1600, "def": 1500},
    "Oscillo Hero #2": {"type": TYPE_THUNDER, "atk": 1000, "def": 500},
    "The Immortal of Thunder": {"type": TYPE_THUNDER, "atk": 1500, "def": 1300},
    "Wattkid": {"type": TYPE_THUNDER, "atk": 1000, "def": 500},
    "Bolt Penguin": {"type": TYPE_THUNDER, "atk": 1100, "def": 800},
    "Twin-Headed Thunder Dragon": {"type": TYPE_THUNDER, "atk": 2800, "def": 2100, "guardian_star": "Pluto"},

    # Dragons
    "Curse of Dragon": {"type": TYPE_DRAGON, "atk": 2000, "def": 1500},
    "Petit Dragon": {"type": TYPE_DRAGON, "atk": 600, "def": 700},
    "Baby Dragon": {"type": TYPE_DRAGON, "atk": 1200, "def": 700},
    "Koumori Dragon": {"type": TYPE_DRAGON, "atk": 1500, "def": 1200},
    "Blackland Fire Dragon": {"type": TYPE_DRAGON, "atk": 1500, "def": 800},
    "Yamatano Dragon Scroll": {"type": TYPE_DRAGON, "atk": 900, "def": 300},
    "One-Eyed Shield Dragon": {"type": TYPE_DRAGON, "atk": 700, "def": 1300},
    "B. Dragon Jungle King": {"type": TYPE_DRAGON, "atk": 2100, "def": 1800},
    "Red-Eyes B. Dragon": {"type": TYPE_DRAGON, "atk": 2400, "def": 2000},
    "Red-Eyes Black Dragon": {"type": TYPE_DRAGON, "atk": 2400, "def": 2000},
    "Blue-Eyes White Dragon": {"type": TYPE_DRAGON, "atk": 3000, "def": 2500},
    "Meteor Dragon": {"type": TYPE_DRAGON, "atk": 1800, "def": 2000},
    "Harpie's Pet Dragon": {"type": TYPE_DRAGON, "atk": 2000, "def": 2500},
    "Meteor Black Dragon": {"type": TYPE_DRAGON, "atk": 3500, "def": 2000, "guardian_star": "Sun"},
    "Spike Seadra": {"type": TYPE_SEA_SERPENT, "atk": 1600, "def": 1300},

    # Equips
    "Shine Palace": {"type": TYPE_EQUIP, "buff": 500, "target": ["Light", TYPE_SEA_SERPENT, TYPE_THUNDER]},
    "Dragon Treasure": {"type": TYPE_EQUIP, "buff": 500, "target": [TYPE_DRAGON]},
    "Dark Energy": {"type": TYPE_EQUIP, "buff": 500, "target": [TYPE_FIEND, TYPE_SPELLCASTER]},
    "Beast Fangs": {"type": TYPE_EQUIP, "buff": 500, "target": [TYPE_BEAST]},
    "Invigoration": {"type": TYPE_EQUIP, "buff": 500, "target": [TYPE_ROCK, TYPE_PYRO]},
    "Electro-Whip": {"type": TYPE_EQUIP, "buff": 500, "target": [TYPE_FEMALE, TYPE_THUNDER]},

    # Powerful Spells
    "Raigeki": {"type": TYPE_SPELL, "atk": 9999},
    "Dark Hole": {"type": TYPE_SPELL, "atk": 9999},
    "Harpie's Feather Duster": {"type": TYPE_SPELL, "atk": 9999},
    "Swords of Revealing Light": {"type": TYPE_SPELL, "atk": 9999},

    # Other common fusion materials
    "Flame Manipulator": {"type": TYPE_PYRO, "atk": 900, "def": 1000},
    "Hinotama Soul": {"type": TYPE_PYRO, "atk": 600, "def": 500},
    "Silver Fang": {"type": TYPE_BEAST, "atk": 1200, "def": 800},
    "Dark Plant": {"type": TYPE_PLANT, "atk": 500, "def": 400},
    "Green Phantom King": {"type": TYPE_PLANT, "atk": 500, "def": 1600},
    "Dissolverock": {"type": TYPE_ROCK, "atk": 900, "def": 1000},
    "Water Omnetics": {"type": TYPE_FEMALE, "atk": 1400, "def": 1200},
    "Ancient Sorcerer": {"type": TYPE_FEMALE, "atk": 1000, "def": 1300},
    "White Dolphin": {"type": TYPE_AQUA, "atk": 500, "def": 400},
}


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
                # Overlay any specific stats passed in dict
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
