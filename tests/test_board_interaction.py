"""
Unit tests for BoardInteraction controller and keyboard navigation command logic.
"""

import unittest
from unittest.mock import MagicMock
from ygbot.board_interaction import BoardInteraction
from ygbot.config import Config


class DummyCDPClient:
    """Mock CDP client that records key dispatches for assertion."""
    def __init__(self):
        self.sent_keys = []

    def send_key(self, key_name: str, delay: float = 0.05):
        self.sent_keys.append(key_name)


class TestBoardInteraction(unittest.TestCase):
    """Verifies board cursor tracking and keyboard command generation."""

    def setUp(self):
        self.mock_cdp = DummyCDPClient()
        self.cfg = Config()
        self.cfg.action_delay = 0.0  # Zero delay for instant tests
        self.board = BoardInteraction(self.mock_cdp, self.cfg)
        self.board.key_delay = 0.0

    def test_focus_hand(self):
        self.assertIsNone(self.board.current_hand_slot)
        self.board.focus_hand()
        self.assertEqual(self.board.current_hand_slot, 0)
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowDown"])

    def test_hand_navigation(self):
        self.board.focus_hand()
        self.mock_cdp.sent_keys.clear()

        # Move to slot 3: should send 3 ArrowRight
        self.board.navigate_to_hand_slot(3)
        self.assertEqual(self.board.current_hand_slot, 3)
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowRight", "ArrowRight", "ArrowRight"])
        self.mock_cdp.sent_keys.clear()

        # Move back to slot 1: should send 2 ArrowLeft
        self.board.navigate_to_hand_slot(1)
        self.assertEqual(self.board.current_hand_slot, 1)
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowLeft", "ArrowLeft"])

    def test_lift_card_for_fusion(self):
        self.board.lift_card_for_fusion()
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowUp"])

    def test_trigger_fusion(self):
        self.board.trigger_fusion()
        self.assertEqual(self.mock_cdp.sent_keys, ["Enter"])

    def test_execute_fusion_sequence(self):
        # Sequence: fuse slot 0 with slot 2
        success = self.board.execute_fusion_sequence([0, 2])
        self.assertTrue(success)
        expected = [
            "ArrowDown",   # focus hand (slot 0)
            "ArrowUp",     # lift slot 0
            "ArrowRight", "ArrowRight", # navigate to slot 2
            "ArrowUp",     # lift slot 2
            "Enter"        # trigger fusion
        ]
        self.assertEqual(self.mock_cdp.sent_keys, expected)

    def test_guardian_star_selection(self):
        self.board.choose_guardian_star(1)
        self.assertEqual(self.mock_cdp.sent_keys[-1], "1")

        self.board.choose_guardian_star(2)
        self.assertEqual(self.mock_cdp.sent_keys[-1], "2")

        self.board.choose_guardian_star("Pluto")
        self.assertEqual(self.mock_cdp.sent_keys[-1], "1")

        self.board.choose_guardian_star("Mercury")
        self.assertEqual(self.mock_cdp.sent_keys[-1], "2")

    def test_end_turn(self):
        self.board.current_hand_slot = 3
        self.board.end_turn()
        self.assertEqual(self.mock_cdp.sent_keys[-1], "e")
        self.assertIsNone(self.board.current_hand_slot)

    def test_place_monster(self):
        self.board.place_monster_on_field(target_zone=2)
        self.assertEqual(self.mock_cdp.sent_keys[-1], "Enter")

    def test_attack_sequence(self):
        self.mock_cdp.sent_keys.clear()
        self.board.execute_attack(player_zone=2, opponent_zone=2)
        self.assertEqual(self.mock_cdp.sent_keys, ["Enter", "Enter", "Enter"])


if __name__ == "__main__":
    unittest.main()
