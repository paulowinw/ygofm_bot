"""
Unit tests for BoardInteraction controller and keyboard navigation command logic.
"""

import unittest
from unittest.mock import MagicMock
from ygbot.pages.game_board_page import GameBoardPage as BoardInteraction, GameState
from ygbot.core.config import Config


class DummyCDPClient:
    """Mock CDP client that records key dispatches and JS evaluations for assertion."""
    def __init__(self):
        self.sent_keys = []
        self.eval_js_calls = []
        self.eval_js_return_value = False

    def send_key(self, key_name: str, delay: float = 0.05):
        self.sent_keys.append(key_name)

    def eval_js(self, js_code: str):
        self.eval_js_calls.append(js_code)
        if callable(self.eval_js_return_value):
            return self.eval_js_return_value(js_code)
        return self.eval_js_return_value


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

    def test_select_fusion_on_card_details_keyboard(self):
        """Verifies that selecting fusion on card details screen dispatches ArrowDown then Enter."""
        self.mock_cdp.sent_keys.clear()
        selected = self.board.select_fusion_on_card_details()
        self.assertTrue(selected)
        # Action: ArrowDown to move to fusion, Enter to confirm
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowDown", "Enter"])

    def test_select_fusion_on_card_details_dom_click(self):
        """Verifies that selecting fusion triggers DOM click on the FUSION button (summon-chain)."""
        self.mock_cdp.eval_js_calls.clear()
        selected = self.board.select_fusion_on_card_details()
        self.assertTrue(selected)
        # Verify JS evaluated targets the summon-chain testid or FUSION button
        self.assertTrue(any("summon-chain" in call or "FUSION" in call for call in self.mock_cdp.eval_js_calls))

    def test_is_fusion_selected_on_card_details(self):
        """Verifies checking if fusion has been selected on card details screen."""
        self.mock_cdp.eval_js_return_value = True
        self.assertTrue(self.board.is_fusion_selected_on_card_details())

        self.mock_cdp.eval_js_return_value = False
        self.assertFalse(self.board.is_fusion_selected_on_card_details())

    def test_is_card_details_open(self):
        """Verifies detection of card details screen."""
        self.mock_cdp.eval_js_return_value = True
        self.assertTrue(self.board.is_card_details_open())

        self.mock_cdp.eval_js_return_value = False
        self.assertFalse(self.board.is_card_details_open())

    def test_dismiss_surrender_modal(self):
        """Verifies that accidental surrender prompts are cancelled."""
        self.mock_cdp.eval_js_calls.clear()
        self.mock_cdp.eval_js_return_value = True
        dismissed = self.board.dismiss_surrender_modal()
        self.assertTrue(dismissed)
        self.assertTrue(any("cancel" in call.lower() for call in self.mock_cdp.eval_js_calls))

    def test_trigger_fusion(self):
        self.board.trigger_fusion()
        self.assertEqual(self.mock_cdp.sent_keys, ["Enter"])

    def test_execute_fusion_sequence(self):
        # Sequence: fuse slot 0 with slot 2
        # For each card: navigate -> open details -> ArrowDown -> Enter (select fusion)
        # Finally: Enter (trigger fusion)
        success = self.board.execute_fusion_sequence([0, 2])
        self.assertTrue(success)
        expected = [
            "ArrowDown",                 # focus hand (slot 0)
            "ArrowDown", "Enter",        # select fusion on card 0 details
            "ArrowRight", "ArrowRight",  # navigate to slot 2
            "ArrowDown", "Enter",        # select fusion on card 2 details
            "Enter"                      # trigger fusion
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


class TestCardDetailsAndScreenStates(unittest.TestCase):
    """Verifies state detection and handling for Card Details and Surrender modals."""

    def setUp(self):
        GameInterface = BoardInteraction
        self.GameState = GameState
        self.mock_cdp = DummyCDPClient()
        self.cfg = Config()
        self.cfg.action_delay = 0.0
        self.game = GameInterface(self.mock_cdp, self.cfg)

    def test_detect_card_details_screen(self):
        """Verifies detect_screen_state correctly identifies CARD_DETAILS."""
        self.mock_cdp.eval_js_return_value = "CARD_DETAILS"
        state = self.game.detect_screen_state()
        self.assertEqual(state, self.GameState.CARD_DETAILS)
        self.assertTrue(self.game.is_card_details_open())

    def test_detect_surrender_modal(self):
        """Verifies detect_screen_state correctly identifies SURRENDER_PROMPT."""
        self.mock_cdp.eval_js_return_value = "SURRENDER_PROMPT"
        state = self.game.detect_screen_state()
        self.assertEqual(state, self.GameState.SURRENDER_PROMPT)

    def test_perform_attack_skips_when_card_details_open(self):
        """Verifies perform_attack_sequence does not blindly attack if stuck at card details."""
        self.mock_cdp.eval_js_return_value = True  # is_card_details_open returns True
        self.mock_cdp.sent_keys.clear()
        self.game.perform_attack_sequence()
        # No attack keys should be dispatched while stuck in card details
        self.assertEqual(self.mock_cdp.sent_keys, [])

    def test_select_fusion_on_card_details_delegation(self):
        """Verifies GameInterface correctly delegates select_fusion_on_card_details to BoardInteraction."""
        self.mock_cdp.sent_keys.clear()
        result = self.game.select_fusion_on_card_details()
        self.assertTrue(result)
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowDown", "Enter"])

    def test_open_and_close_card_details(self):
        """Verifies opening card details sends Enter and closing sends Escape."""
        self.mock_cdp.sent_keys.clear()
        self.game.open_card_details()
        self.assertEqual(self.mock_cdp.sent_keys, ["Enter"])

        self.mock_cdp.sent_keys.clear()
        self.game.close_card_details()
        self.assertEqual(self.mock_cdp.sent_keys, ["Escape"])

    def test_focus_next_hand_card(self):
        """Verifies focus_next_hand_card sends ArrowRight and increments slot."""
        self.game.current_hand_slot = 1
        self.mock_cdp.sent_keys.clear()
        self.game.focus_next_hand_card()
        self.assertEqual(self.mock_cdp.sent_keys, ["ArrowRight"])
        self.assertEqual(self.game.current_hand_slot, 2)

    def test_inspect_card_at_slot_keyboard_sequence(self):
        """Verifies inspect_card_at_slot opens with Enter, reads details, and closes with Escape."""
        self.game.current_hand_slot = 0
        self.mock_cdp.sent_keys.clear()
        self.mock_cdp.eval_js_return_value = {
            "name": "Meteor Dragon",
            "atk": 1800,
            "def": 2000,
            "type": "Dragon",
            "star": "Sun",
        }
        data = self.game.inspect_card_at_slot(slot_index=0)
        self.assertEqual(data["name"], "Meteor Dragon")
        self.assertEqual(data["atk"], 1800)
        self.assertEqual(self.mock_cdp.sent_keys, ["Enter", "Escape"])


if __name__ == "__main__":
    unittest.main()
