"""
Unit tests for discrete Page Actions (Action Sequencer Pattern) and POM integration.
"""

import unittest
from unittest.mock import MagicMock, patch
from ygbot.actions.base_action import BaseAction
from ygbot.actions.game_board.inspect_hand_action import InspectHandAction
from ygbot.actions.game_board.fusion_action import FusionAction, FusionEngine
from ygbot.actions.game_board.summon_action import SummonAction
from ygbot.actions.game_board.attack_action import AttackAction
from ygbot.actions.game_board.end_turn_action import EndTurnAction
from ygbot.actions.lobby.start_duel_action import StartDuelAction
from ygbot.pages.lobby_page import LobbyPage
from ygbot.pages.game_board_page import GameBoardPage, GameState
from ygbot.features.cards.models import MonsterCard
from ygbot.features.cards.card_type import CardType
from ygbot.features.fusion.result import FusionResult
from ygbot.core.utils import format_cards_table, print_cards_table


class MockBoardPage:
    """Mock GameBoardPage for testing action execution."""
    def __init__(self):
        self.keyboard_events = []
        self.inspected_slots = []
        self.clicked_slots = []
        self.fusion_triggered = False
        self.attack_executed = False
        self.turn_ended = False
        self.guardian_star_chosen = None
        self.placed_zone = None
        self.screen_state = GameState.IN_DUEL
        self.current_hand_slot = None

    def focus_hand(self, turn_number: int = 1):
        self.keyboard_events.append("ArrowDown")
        self.current_hand_slot = 0

    def open_card_details(self, turn_number: int = 1) -> bool:
        self.keyboard_events.append("Enter")
        return True

    def close_card_details(self, turn_number: int = 1) -> bool:
        self.keyboard_events.append("Escape")
        return True

    def focus_next_hand_card(self, turn_number: int = 1) -> bool:
        self.keyboard_events.append("ArrowRight")
        if self.current_hand_slot is not None:
            self.current_hand_slot += 1
        return True

    def read_opened_card_details(self, slot_index: int = 0, turn_number: int = 1):
        self.inspected_slots.append(slot_index)
        cards = [
            {"name": "Bolt Escargot", "atk": 1400, "def": 1500, "star": "Pluto", "type": "Thunder"},
            {"name": "Curse of Dragon", "atk": 2000, "def": 1500, "star": "Mars", "type": "Dragon"},
            {"name": "Dragon Treasure", "atk": None, "def": None, "star": None, "type": "Equip"},
            {"name": "Baby Dragon", "atk": 1200, "def": 700, "star": "Sun", "type": "Dragon"},
            {"name": "Silver Fang", "atk": 1200, "def": 800, "star": "Moon", "type": "Beast"},
        ]
        return cards[slot_index]

    def inspect_card_at_slot(self, slot_index: int, turn_number: int = 1):
        self.open_card_details(turn_number=turn_number)
        data = self.read_opened_card_details(slot_index=slot_index, turn_number=turn_number)
        self.close_card_details(turn_number=turn_number)
        return data

    def click_card_at_slot(self, slot_index: int, turn_number: int = 1) -> bool:
        self.clicked_slots.append(slot_index)
        return True

    def trigger_fusion(self, turn_number: int = 1) -> bool:
        self.fusion_triggered = True
        return True

    def detect_screen_state(self) -> str:
        return self.screen_state

    def choose_guardian_star(self, star: str, turn_number: int = 1) -> bool:
        self.guardian_star_chosen = star
        return True

    def place_monster_on_field(self, target_zone: int = 0, turn_number: int = 1) -> bool:
        self.placed_zone = target_zone
        return True

    def execute_attack(self, player_zone: int = 2, opponent_zone: int = 2, turn_number: int = 1) -> bool:
        self.attack_executed = True
        return True

    def end_turn(self, turn_number: int = 1) -> bool:
        self.turn_ended = True
        return True

    def dismiss_surrender_modal(self, turn_number: int = 1) -> bool:
        return True


class MockLobbyPage:
    """Mock LobbyPage for testing lobby actions."""
    def __init__(self):
        self.selected_opponent = None
        self.started_duel = False
        self.duel_again_clicked = False

    def select_opponent(self, opponent_name: str, turn_number: int = 1) -> bool:
        self.selected_opponent = opponent_name
        return True

    def click_start_duel(self, turn_number: int = 1) -> bool:
        self.started_duel = True
        return True

    def start_duel(self, opponent_name: str, turn_number: int = 1) -> bool:
        self.selected_opponent = opponent_name
        self.started_duel = True
        return True

    def click_duel_again(self, turn_number: int = 1) -> bool:
        self.duel_again_clicked = True
        return True


class TestPageActions(unittest.TestCase):
    """Verifies that actions organized by page execute correctly."""

    def test_inspect_hand_action_opens_cards_one_by_one_via_keyboard(self):
        mock_page = MockBoardPage()
        action = InspectHandAction(mock_page)

        self.assertEqual(len(action.cards_in_hand), 0)
        self.assertFalse(action.has_inspected_initial_board)

        # Execute inspection
        with patch("ygbot.actions.game_board.inspect_hand_action.print_cards_table") as mock_print:
            hand = action.execute(turn_number=1)

            # Verifies exact keyboard sequence:
            # ArrowDown (focus first card)
            # Enter -> Escape -> ArrowRight (repeat across all cards)
            expected_keys = [
                "ArrowDown",
                "Enter", "Escape", "ArrowRight",
                "Enter", "Escape", "ArrowRight",
                "Enter", "Escape", "ArrowRight",
                "Enter", "Escape", "ArrowRight",
                "Enter", "Escape"
            ]
            self.assertEqual(mock_page.keyboard_events, expected_keys)

            # Verifies that all 5 slots were read from opened box
            self.assertEqual(mock_page.inspected_slots, [0, 1, 2, 3, 4])

            # Verifies cards are stored in variable
            self.assertEqual(len(hand), 5)
            self.assertEqual(action.cards_in_hand, hand)
            self.assertTrue(action.has_inspected_initial_board)
            self.assertEqual(hand[0].name, "Bolt Escargot")
            self.assertEqual(hand[1].name, "Curse of Dragon")
            self.assertEqual(hand[0].atk, 1400)
            self.assertEqual(hand[0].def_, 1500)
            self.assertEqual(hand[0].guardian_star_primary, "Pluto")

            # Verifies that console table printing was triggered
            mock_print.assert_called_once_with(action.cards_in_hand, title="TURN 1 - HAND CARDS INSPECTED")

        # Test reset for new duel
        action.reset()
        self.assertEqual(len(action.cards_in_hand), 0)
        self.assertFalse(action.has_inspected_initial_board)

    def test_fusion_action_solves_hand_executes_and_logs_stats(self):
        mock_page = MockBoardPage()
        fusion_action = FusionAction(mock_page, strategy="THTD")

        hand = ["Bolt Escargot", "Curse of Dragon", "Silver Fang"]
        result = fusion_action.solve_hand(hand)

        self.assertEqual(result.play_name, "Twin-Headed Thunder Dragon")
        self.assertEqual(result.sequence, [0, 1])

        # Execute fusion and capture console logs
        with patch("ygbot.actions.game_board.fusion_action.log") as mock_log:
            success = fusion_action.execute(result, turn_number=2)
            self.assertTrue(success)
            self.assertEqual(mock_page.clicked_slots, [0, 1])
            self.assertTrue(mock_page.fusion_triggered)

            # Verifies that name, ATK, and DEF are logged
            logged_successes = [call.args[0] for call in mock_log.call_args_list if call.args[1] == "SUCCESS"]
            self.assertTrue(any("Twin-Headed Thunder Dragon" in msg for msg in logged_successes))
            self.assertTrue(any("ATK:" in msg and "2800" in msg for msg in logged_successes))
            self.assertTrue(any("DEF:" in msg and "2100" in msg for msg in logged_successes))

    def test_fusion_action_accepts_raw_hand_directly_in_execute(self):
        mock_page = MockBoardPage()
        fusion_action = FusionAction(mock_page, strategy="THTD")

        hand = ["Bolt Escargot", "Curse of Dragon"]
        with patch("ygbot.actions.game_board.fusion_action.log"):
            success = fusion_action.execute(hand, turn_number=1)
            self.assertTrue(success)
            self.assertEqual(mock_page.clicked_slots, [0, 1])
            self.assertTrue(mock_page.fusion_triggered)

    def test_start_duel_action(self):
        mock_lobby = MockLobbyPage()
        action = StartDuelAction(mock_lobby)

        success = action.execute("High Mage Martis", turn_number=1)
        self.assertTrue(success)
        self.assertEqual(mock_lobby.selected_opponent, "High Mage Martis")
        self.assertTrue(mock_lobby.started_duel)

    def test_summon_action(self):
        mock_page = MockBoardPage()
        mock_page.screen_state = GameState.GUARDIAN_STAR
        action = SummonAction(mock_page)

        success = action.execute(guardian_star="Pluto", target_zone=1, turn_number=1)
        self.assertTrue(success)
        self.assertEqual(mock_page.guardian_star_chosen, "Pluto")
        self.assertEqual(mock_page.placed_zone, 1)

    def test_attack_and_end_turn_actions(self):
        mock_page = MockBoardPage()
        attack_action = AttackAction(mock_page)
        end_turn_action = EndTurnAction(mock_page)

        atk_success = attack_action.execute(player_zone=2, opponent_zone=2, turn_number=1)
        self.assertTrue(atk_success)
        self.assertTrue(mock_page.attack_executed)

        end_success = end_turn_action.execute(turn_number=1)
        self.assertTrue(end_success)
        self.assertTrue(mock_page.turn_ended)

    def test_table_formatting_utility(self):
        cards = [
            MonsterCard(name="Twin-Headed Thunder Dragon", card_type=CardType.THUNDER, atk=2800, def_=2100, index=0),
            "Bolt Escargot",
            {"slot": 3, "name": "Curse of Dragon", "type": "Dragon", "atk": 2000, "def": 1500, "star": "Mars"},
        ]
        table_str = format_cards_table(cards)
        self.assertIn("Twin-Headed Thunder Dragon", table_str)
        self.assertIn("Bolt Escargot", table_str)
        self.assertIn("Curse of Dragon", table_str)
        self.assertIn("2800", table_str)
        self.assertIn("2100", table_str)

        # Empty cards test
        self.assertEqual(format_cards_table([]), "(No cards in hand)")


if __name__ == "__main__":
    unittest.main()
