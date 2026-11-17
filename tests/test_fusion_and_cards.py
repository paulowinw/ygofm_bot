"""
Unit tests for the refactored Card models, CardType, CardRegistry,
Fusion Strategies, and FusionEngine.
"""

import unittest
from ygbot.cards import (
    CardType,
    Card,
    MonsterCard,
    EquipCard,
    SpellCard,
    CardRegistry,
    KNOWN_CARDS,
    TYPE_DRAGON,
    TYPE_THUNDER,
)
from ygbot.fusion import (
    FusionEngine,
    FusionResult,
    THTDFusionStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)


class TestCardTypesAndModels(unittest.TestCase):
    """Verifies CardType domain properties and Card model behaviors."""

    def test_card_type_properties(self):
        dragon = CardType.DRAGON
        self.assertTrue(dragon.is_monster)
        self.assertFalse(dragon.is_equip)
        self.assertFalse(dragon.is_spell)

        equip = CardType.EQUIP
        self.assertFalse(equip.is_monster)
        self.assertTrue(equip.is_equip)

        spell = CardType.SPELL
        self.assertFalse(spell.is_monster)
        self.assertTrue(spell.is_spell)

    def test_card_type_from_str(self):
        self.assertEqual(CardType.from_str("Dragon"), CardType.DRAGON)
        self.assertEqual(CardType.from_str("thunder"), CardType.THUNDER)
        self.assertEqual(CardType.from_str("unknown_xyz"), CardType.UNKNOWN)

    def test_monster_card_creation(self):
        monster = MonsterCard(name="Curse of Dragon", card_type=CardType.DRAGON, atk=2000, def_=1500, index=2)
        self.assertEqual(monster.name, "Curse of Dragon")
        self.assertEqual(monster.atk, 2000)
        self.assertTrue(monster.is_monster)
        self.assertEqual(monster.index, 2)
        
        # Test dictionary conversion
        d = monster.to_dict()
        self.assertEqual(d["name"], "Curse of Dragon")
        self.assertEqual(d["type"], "Dragon")
        self.assertEqual(d["atk"], 2000)

    def test_equip_card_affinity(self):
        dragon_treasure = EquipCard(
            name="Dragon Treasure",
            card_type=CardType.EQUIP,
            buff=500,
            target_types=["Dragon"]
        )
        dragon = MonsterCard(name="Baby Dragon", card_type=CardType.DRAGON)
        thunder = MonsterCard(name="Bolt Escargot", card_type=CardType.THUNDER)

        self.assertTrue(dragon_treasure.can_equip_to(dragon))
        self.assertFalse(dragon_treasure.can_equip_to(thunder))

    def test_spell_card(self):
        raigeki = SpellCard(name="Raigeki", atk=9999)
        self.assertTrue(raigeki.is_spell)
        self.assertFalse(raigeki.is_monster)


class TestCardRegistry(unittest.TestCase):
    """Verifies the CardRegistry factory and heuristic detection."""

    def setUp(self):
        self.registry = CardRegistry.get_instance()

    def test_known_card_lookup(self):
        card = self.registry.create_card_from_name("Curse of Dragon", index=0)
        self.assertIsInstance(card, MonsterCard)
        self.assertEqual(card.card_type, CardType.DRAGON)
        self.assertEqual(card.atk, 2000)

        shine = self.registry.create_card_from_name("Shine Palace", index=4)
        self.assertIsInstance(shine, EquipCard)
        self.assertEqual(shine.buff, 500)

    def test_heuristic_parsing(self):
        unknown_dragon = self.registry.create_card_from_name("Mystic Dragon Knight", index=1)
        self.assertIsInstance(unknown_dragon, MonsterCard)
        self.assertEqual(unknown_dragon.card_type, CardType.DRAGON)

        unknown_thunder = self.registry.create_card_from_name("Electric Beast", index=2)
        self.assertIsInstance(unknown_thunder, MonsterCard)
        self.assertEqual(unknown_thunder.card_type, CardType.THUNDER)

    def test_from_any_adapter(self):
        # From string
        c1 = self.registry.from_any("Kaminari Attack", index=0)
        self.assertEqual(c1.card_type, CardType.THUNDER)

        # From dict
        c2 = self.registry.from_any({"name": "Custom Dragon", "type": "Dragon", "atk": 2500}, index=1)
        self.assertIsInstance(c2, MonsterCard)
        self.assertEqual(c2.atk, 2500)

        # From Card instance
        existing = MonsterCard(name="Existing", card_type=CardType.WARRIOR)
        c3 = self.registry.from_any(existing, index=3)
        self.assertEqual(c3.index, 3)


class TestFusionStrategiesAndEngine(unittest.TestCase):
    """Verifies the Strategy Pattern implementation in FusionEngine."""

    def setUp(self):
        self.engine = FusionEngine(strategy="THTD")

    def test_thtd_strategy_execution(self):
        # Hand with Thunder and Dragon
        hand = [
            "Bolt Escargot",   # Thunder (idx 0)
            "Curse of Dragon", # Dragon (idx 1)
            "Petit Dragon",    # Extra Dragon (idx 2)
            "Shine Palace",    # Equip (idx 3)
            "Silver Fang",     # Beast (idx 4)
        ]
        result = self.engine.solve_hand(hand)
        self.assertIsInstance(result, FusionResult)
        
        # Test tuple unpacking
        seq, name, atk = result
        self.assertEqual(name, "Twin-Headed Thunder Dragon")
        self.assertEqual(seq[0], 0)  # Thunder first
        self.assertEqual(seq[1], 1)  # Dragon second
        self.assertIn(2, seq)        # Chained extra dragon
        self.assertIn(3, seq)        # Chained equip
        self.assertGreaterEqual(atk, 2800)

    def test_equip_buff_strategy(self):
        # Hand with no Thunder, but Monster and Equip
        hand = [
            "Spike Seadra",  # Sea Serpent (idx 0)
            "Shine Palace",  # Equip (idx 1)
            "Silver Fang",   # Beast (idx 2)
            "Dark Plant",    # Plant (idx 3)
            "Flame Manipulator" # Pyro (idx 4)
        ]
        seq, name, atk = self.engine.solve_hand(hand)
        self.assertIn("Equipped", name)
        self.assertEqual(seq[0], 0)  # Spike Seadra
        self.assertEqual(seq[1], 1)  # Shine Palace
        self.assertEqual(atk, 1600 + 500)

    def test_elemental_fusion_strategy(self):
        # Hand with Dragon + Plant -> Black Forest Dragon
        hand = [
            "Curse of Dragon",  # Dragon (idx 0)
            "Dark Plant",       # Plant (idx 1)
            "Silver Fang",      # Beast (idx 2)
        ]
        seq, name, atk = self.engine.solve_hand(hand)
        self.assertEqual(name, "Black Forest Dragon")
        self.assertEqual(seq, [0, 1])
        self.assertEqual(atk, 2100)

        # Hand with Beast + Pyro -> Flame Cerebrus
        hand_beast_pyro = [
            "Silver Fang",       # Beast (idx 0)
            "Flame Manipulator", # Pyro (idx 1)
        ]
        seq, name, atk = self.engine.solve_hand(hand_beast_pyro)
        self.assertEqual(name, "Flame Cerebrus")
        self.assertEqual(seq, [0, 1])
        self.assertEqual(atk, 2100)

    def test_highest_atk_fallback(self):
        # Hand with no compatible fusions
        hand = [
            "White Dolphin",  # 500 ATK (idx 0)
            "Silver Fang",    # 1200 ATK (idx 1)
        ]
        seq, name, atk = self.engine.solve_hand(hand)
        self.assertEqual(name, "Silver Fang")
        self.assertEqual(seq, [1])
        self.assertEqual(atk, 1200)

    def test_empty_hand(self):
        seq, name, atk = self.engine.solve_hand([])
        self.assertEqual(seq, [])
        self.assertEqual(name, "Empty Hand")
        self.assertEqual(atk, 0)


if __name__ == "__main__":
    unittest.main()
