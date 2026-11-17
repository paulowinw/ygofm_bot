"""
Yu-Gi-Oh! Forbidden Memories - Known Cards Database.

Artifact: Known Cards Catalog
Separated from the registry to ensure Single Responsibility and clean domain boundaries.
"""

from typing import Dict, Any
from .card_type import (
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

# Canonical card registry of stats, archetypes, and affinities in Forbidden Memories
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
