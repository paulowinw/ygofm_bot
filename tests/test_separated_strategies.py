"""
Unit tests for separated Fusion Strategies and FusionEngine Page Object delegation.
Verifies Single Responsibility Principle (SRP) and Open/Closed Principle (OCP).
"""

import unittest
from ygbot.features.cards.models import MonsterCard, EquipCard, SpellCard
from ygbot.features.cards.card_type import CardType
from ygbot.features.fusion.result import FusionResult
from ygbot.features.fusion.strategies.meteor_black_dragon import MeteorBlackDragonStrategy
from ygbot.features.fusion.strategies.thtd_strategy import THTDFusionStrategy
from ygbot.features.fusion.strategies.discard_cycle_strategy import DiscardAndCycleStrategy
from ygbot.features.fusion.strategies.equip_buff_strategy import EquipBuffStrategy
from ygbot.features.fusion.strategies.elemental_fusion_strategy import ElementalFusionStrategy
from ygbot.features.fusion.strategies.highest_atk_strategy import HighestAtkStrategy
from ygbot.actions.game_board.fusion_action import FusionAction as FusionEngine


class MockBoardPage:
    """Mock GameBoardPage to test FusionEngine interactions."""
    def __init__(self):
        self.clicked_slots = []
        self.fusion_triggered = False

    def click_card_at_slot(self, slot_index: int, turn_number: int = 1) -> bool:
        self.clicked_slots.append(slot_index)
        return True

    def trigger_fusion(self, turn_number: int = 1) -> bool:
        self.fusion_triggered = True
        return True


class TestSeparatedFusionStrategies(unittest.TestCase):
    """Verifies that each separated strategy artifact behaves correctly in isolation."""

    def test_meteor_black_dragon_strategy(self):
        strat = MeteorBlackDragonStrategy()
        self.assertEqual(strat.name, "MeteorBlackDragon")

        hand = [
            MonsterCard(name="Red-Eyes B. Dragon", card_type=CardType.DRAGON, atk=2400, index=0),
            MonsterCard(name="Meteor Dragon", card_type=CardType.DRAGON, atk=1800, index=1),
            EquipCard(name="Dragon Treasure", card_type=CardType.EQUIP, buff=500, target_types=["Dragon"], index=2),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        self.assertEqual(res.sequence, [0, 1, 2])
        self.assertEqual(res.play_name, "Meteor Black Dragon")
        self.assertEqual(res.estimated_atk, 4000)
        self.assertEqual(res.guardian_star, "Sun")

    def test_thtd_strategy(self):
        strat = THTDFusionStrategy()
        self.assertEqual(strat.name, "THTD")

        hand = [
            MonsterCard(name="Bolt Escargot", card_type=CardType.THUNDER, atk=1400, index=0),
            MonsterCard(name="Curse of Dragon", card_type=CardType.DRAGON, atk=2000, index=1),
            EquipCard(name="Dragon Treasure", card_type=CardType.EQUIP, buff=500, target_types=["Dragon"], index=2),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        self.assertEqual(res.sequence, [0, 1, 2])
        self.assertEqual(res.play_name, "Twin-Headed Thunder Dragon")
        self.assertEqual(res.estimated_atk, 3300)
        self.assertEqual(res.guardian_star, "Pluto")

    def test_discard_cycle_strategy(self):
        strat = DiscardAndCycleStrategy()
        self.assertEqual(strat.name, "DiscardAndCycle")

        # Hand with multiple duplicate dragons and no thunder: should discard extra dragon
        hand = [
            MonsterCard(name="Baby Dragon", card_type=CardType.DRAGON, atk=1200, index=0),
            MonsterCard(name="Curse of Dragon", card_type=CardType.DRAGON, atk=2000, index=1),
            MonsterCard(name="Petit Dragon", card_type=CardType.DRAGON, atk=600, index=2),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        # Curse of Dragon is keeper (2000 ATK), other two discarded, then keeper appended
        self.assertIn(0, res.sequence)
        self.assertIn(2, res.sequence)
        self.assertEqual(res.sequence[-1], 1)

    def test_equip_buff_strategy(self):
        strat = EquipBuffStrategy()
        self.assertEqual(strat.name, "EquipBuff")

        hand = [
            MonsterCard(name="Curse of Dragon", card_type=CardType.DRAGON, atk=2000, index=0),
            EquipCard(name="Dragon Treasure", card_type=CardType.EQUIP, buff=500, target_types=["Dragon"], index=1),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        self.assertEqual(res.sequence, [0, 1])
        self.assertEqual(res.estimated_atk, 2500)

    def test_elemental_fusion_strategy(self):
        strat = ElementalFusionStrategy()
        self.assertEqual(strat.name, "ElementalFusion")

        hand = [
            MonsterCard(name="Baby Dragon", card_type=CardType.DRAGON, index=0),
            MonsterCard(name="Dark Plant", card_type=CardType.PLANT, index=1),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        self.assertEqual(res.sequence, [0, 1])
        self.assertEqual(res.play_name, "Black Forest Dragon")
        self.assertEqual(res.estimated_atk, 2100)

    def test_highest_atk_strategy(self):
        strat = HighestAtkStrategy()
        self.assertEqual(strat.name, "HighestAtk")

        hand = [
            MonsterCard(name="Baby Dragon", card_type=CardType.DRAGON, atk=1200, index=0),
            MonsterCard(name="Curse of Dragon", card_type=CardType.DRAGON, atk=2000, index=1),
        ]
        res = strat.evaluate(hand)
        self.assertIsNotNone(res)
        self.assertEqual(res.sequence, [1])
        self.assertEqual(res.play_name, "Curse of Dragon")
        self.assertEqual(res.estimated_atk, 2000)

    def test_fusion_engine_delegates_to_page_object(self):
        """Verifies that FusionEngine asks the Page Object to click specific card coordinates."""
        engine = FusionEngine(strategy="THTD")
        mock_board = MockBoardPage()

        hand = ["Bolt Escargot", "Curse of Dragon"]
        result = engine.solve_hand(hand)
        self.assertEqual(result.play_name, "Twin-Headed Thunder Dragon")

        success = engine.execute_fusion(result, board_page=mock_board, turn_number=3)
        self.assertTrue(success)
        self.assertEqual(mock_board.clicked_slots, [0, 1])
        self.assertTrue(mock_board.fusion_triggered)


if __name__ == "__main__":
    unittest.main()
