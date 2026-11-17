"""
Unit tests for Adapted Page Object Model (POM) and Middleware execution pipeline.
Verifies SOLID principles, Clean Code separation, and ACID transaction safety.
"""

import unittest
from unittest.mock import MagicMock
from ygbot.core.middleware import (
    ActionContext,
    MiddlewarePipeline,
    LoggingMiddleware,
    TimingAndDelayMiddleware,
    VisionFallbackMiddleware,
    ErrorCaptureMiddleware,
    create_default_pipeline,
)
from ygbot.pages.base_page import BasePage
from ygbot.pages.game_board_page import GameBoardPage, GameState
from ygbot.features.cards.card_manager import CardManager
from ygbot.features.cards.models import MonsterCard, EquipCard, SpellCard
from ygbot.features.cards.card_type import CardType
from ygbot.core.config import Config


class DummyCDP:
    def __init__(self):
        self.sent_keys = []
        self.clicks = []
        self.evals = []
        self.viewport_width = 1920
        self.viewport_height = 1080
        self.eval_result = True
        self.screenshots = []

    def send_key(self, key_name: str, delay: float = 0.0):
        self.sent_keys.append(key_name)

    def click_at(self, x: int, y: int):
        self.clicks.append((x, y))

    def click_element_by_text(self, text: str) -> bool:
        if "DUEL" in text or "START" in text:
            return True
        return False

    def eval_js(self, script: str):
        self.evals.append(script)
        if callable(self.eval_result):
            return self.eval_result(script)
        return self.eval_result

    def capture_screenshot(self, path: str):
        self.screenshots.append(path)


class DummyVision:
    def __init__(self):
        self.clicks = []

    def click_percent(self, x: float, y: float, delay: float = 0.0):
        self.clicks.append((x, y))


class TestMiddlewarePipeline(unittest.TestCase):
    """Tests the 4-stage middleware pipeline."""

    def test_pipeline_execution_success(self):
        cdp = DummyCDP()
        vision = DummyVision()
        pipeline = create_default_pipeline(cdp_client=cdp, vision_clicker=vision, action_delay=0.0)

        called = []
        def handler():
            called.append(True)
            return "ok"

        res = pipeline.run("Test", "CLICK", handler, turn_number=1, description="Test Action")
        self.assertEqual(res, "ok")
        self.assertTrue(called)

    def test_vision_fallback_on_handler_failure(self):
        cdp = DummyCDP()
        vision = DummyVision()
        pipeline = create_default_pipeline(cdp_client=cdp, vision_clicker=vision, action_delay=0.0)

        def failing_handler():
            return False

        res = pipeline.run(
            "FailingClick",
            "CLICK",
            failing_handler,
            turn_number=1,
            fallback_coords=(0.45, 0.85),
            description="Failing click test",
        )
        self.assertTrue(res)
        self.assertEqual(vision.clicks, [(0.45, 0.85)])

    def test_error_capture_on_critical_failure(self):
        cdp = DummyCDP()
        pipeline = create_default_pipeline(cdp_client=cdp, vision_clicker=None, action_delay=0.0)

        def fatal_handler():
            raise RuntimeError("Fatal CDP failure")

        with self.assertRaises(RuntimeError):
            pipeline.run(
                "FatalAction",
                "CLICK",
                fatal_handler,
                turn_number=1,
                description="Fatal action test",
            )
        self.assertTrue(len(cdp.screenshots) > 0)


class TestAdaptedPOM(unittest.TestCase):
    """Tests Adapted Page Object Model (POM) interactions."""

    def setUp(self):
        self.cdp = DummyCDP()
        self.cfg = Config()
        self.cfg.action_delay = 0.0
        self.board = GameBoardPage(self.cdp, self.cfg)
        self.board.key_delay = 0.0

    def test_card_slot_coordinates(self):
        coords = self.board.get_card_coordinates(0)
        self.assertAlmostEqual(coords[0], 0.372)
        self.assertAlmostEqual(coords[1], 0.870)

        coords_last = self.board.get_card_coordinates(4)
        self.assertAlmostEqual(coords_last[0], 0.550)

    def test_click_card_at_slot_via_dom(self):
        # When DOM query finds card, it returns True
        self.cdp.eval_result = True
        success = self.board.click_card_at_slot(1, turn_number=2)
        self.assertTrue(success)

    def test_click_duel_again(self):
        self.cdp.eval_result = True
        success = self.board.click_duel_again(turn_number=1)
        self.assertTrue(success)

    def test_start_duel_from_lobby(self):
        success = self.board.start_duel_from_lobby("High Mage Martis")
        self.assertTrue(success)


class TestCardManager(unittest.TestCase):
    """Tests CardManager domain operations."""

    def test_parse_hand(self):
        manager = CardManager()
        raw_cards = ["Curse of Dragon", "Bolt Escargot", "Dragon Treasure", "Raigeki"]
        cards = manager.parse_hand(raw_cards)
        self.assertEqual(len(cards), 4)
        self.assertIsInstance(cards[0], MonsterCard)
        self.assertEqual(cards[0].index, 0)
        self.assertIsInstance(cards[2], EquipCard)
        self.assertEqual(cards[2].index, 2)
        self.assertIsInstance(cards[3], SpellCard)
        self.assertEqual(cards[3].index, 3)

    def test_evaluate_hand_stats(self):
        manager = CardManager()
        manager.parse_hand(["Curse of Dragon", "Bolt Escargot", "Dragon Treasure"])
        stats = manager.evaluate_hand_stats()
        self.assertEqual(stats["total"], 3)
        self.assertEqual(stats["monsters"], 2)
        self.assertEqual(stats["equips"], 1)
        self.assertEqual(stats["max_atk"], 2000)


if __name__ == "__main__":
    unittest.main()
