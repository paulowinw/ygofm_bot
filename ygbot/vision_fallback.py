"""
Vision / Screen-coordinate clicker fallback.
Provides PyAutoGUI or direct screen clicking if the user prefers desktop mouse control.
"""

import time
from typing import Optional, Tuple
from .config import Config
from .utils import log

class ScreenClicker:
    """Alternative screen-based automation controller."""

    def __init__(self, config: Config):
        self.cfg = config
        self.has_pyautogui = False
        try:
            import pyautogui
            self.pyautogui = pyautogui
            self.has_pyautogui = True
            # Get screen resolution
            self.screen_width, self.screen_height = pyautogui.size()
        except ImportError:
            self.pyautogui = None
            self.screen_width = 1920
            self.screen_height = 1080

    def click_percent(self, x_pct: float, y_pct: float, delay: float = 0.1):
        """Clicks at normalized percentage coordinates on desktop screen."""
        if not self.has_pyautogui:
            log("PyAutoGUI is not installed. To use screen-based clicking, install it via: pip install pyautogui", "WARN")
            return
        
        target_x = int(x_pct * self.screen_width)
        target_y = int(y_pct * self.screen_height)
        self.pyautogui.click(target_x, target_y)
        time.sleep(delay)

    def click_card(self, index: int):
        """Clicks card slot on screen."""
        if 0 <= index < len(self.cfg.hand_cards):
            coord = self.cfg.hand_cards[index]
            self.click_percent(coord[0], coord[1], delay=self.cfg.action_delay)

    def select_guardian_star(self, choice: str = "Pluto"):
        """Clicks guardian star on screen."""
        coord = self.cfg.guardian_star_coords.get(choice, self.cfg.guardian_star_coords["Pluto"])
        self.click_percent(coord[0], coord[1], delay=0.5)

    def duel_again(self):
        """Clicks duel again on screen."""
        bx, by = self.cfg.duel_again_button
        self.click_percent(bx, by, delay=1.0)
