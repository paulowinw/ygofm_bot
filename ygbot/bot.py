"""
Autonomous Bot Controller for Forbidden Memories Online.

Main Orchestration Loop (Runner):
Manages the rolling farming loop, state machine transitions,
and executes discrete actions organized by page:
- Lobby actions: StartDuelAction (interacts with LobbyPage)
- Game board actions: InspectHandAction, FusionAction, SummonAction, AttackAction, EndTurnAction (interacts with GameBoardPage)
"""

import time
import sys
from typing import Optional, List
from .core.config import Config
from .core.cdp_client import CDPClient
from .pages.base_page import BasePage
from .pages.lobby_page import LobbyPage
from .pages.game_board_page import GameBoardPage, GameState
from .features.cards.models import Card
from .features.cards.card_manager import CardManager
from .actions.game_board import (
    InspectHandAction,
    FusionAction,
    SummonAction,
    AttackAction,
    EndTurnAction,
)
from .actions.lobby import StartDuelAction
from .core.utils import log, Colors, format_duration


class YGBot:
    """
    Main autonomous duel runner orchestrating the rolling console loop.
    Coordinates discrete actions organized by page:
    - Lobby actions: StartDuelAction
    - Game board actions: InspectHandAction, FusionAction, SummonAction, AttackAction, EndTurnAction
    """

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config.load()
        self.cdp = CDPClient(host=self.cfg.chrome_host, port=self.cfg.chrome_port)
        
        # Page Object Model (POM) wrappers
        self.lobby = LobbyPage(self.cdp, self.cfg)
        self.board = GameBoardPage(self.cdp, self.cfg)
        self.cards = CardManager()
        
        # Actions organized by page
        self.start_duel_action = StartDuelAction(self.lobby)
        self.inspect_hand_action = InspectHandAction(self.board, self.cards)
        self.fusion_action = FusionAction(self.board, strategy=self.cfg.strategy)
        self.summon_action = SummonAction(self.board)
        self.attack_action = AttackAction(self.board)
        self.end_turn_action = EndTurnAction(self.board)

        # Variables storing card state and board tracking
        self.cards_in_hand: List[Card] = []
        self.is_board_first_open: bool = True

        # Stats & counters
        self.duels_played = 0
        self.duels_won = 0
        self.start_time = 0.0
        self.current_duel_start = 0.0
        self.turn_number = 1

    def connect_to_chrome(self) -> bool:
        """Verifies Chrome is running with remote debugging and attaches to game tab."""
        log(f"Checking Google Chrome on {self.cfg.chrome_host}:{self.cfg.chrome_port}...", "INFO")
        
        if not self.cdp.is_chrome_running():
            log(f"Could not connect to Chrome on port {self.cfg.chrome_port}.", "ERROR")
            log("Please launch Google Chrome with remote debugging enabled:", "WARN")
            log(f"  {Colors.BOLD}./launch_chrome.sh{Colors.END}", "WARN")
            log(f"  OR: {Colors.BOLD}google-chrome --remote-debugging-port={self.cfg.chrome_port} --user-data-dir=\"$HOME/.config/ygbot-chrome\"{Colors.END}", "WARN")
            return False

        log("Chrome debugging port detected! Searching for game tab...", "SUCCESS")
        tab = self.cdp.find_game_tab([self.cfg.target_url_pattern, self.cfg.alt_url_pattern, "ygofm", "duel", "forbidden"])
        
        if not tab:
            log(f"No active game tab found matching 'Forbidden Memories' or '{self.cfg.target_url_pattern}'.", "WARN")
            tabs = self.cdp.get_tabs()
            if tabs:
                log(f"Attaching to active tab: {tabs[0].get('title', 'Unknown')} ({tabs[0].get('url', '')})", "INFO")
                tab = tabs[0]
            else:
                log("No open tabs found in Chrome.", "ERROR")
                return False

        log(f"Connected to tab: '{tab.get('title')}'", "SUCCESS")
        log(f"Tab URL: {tab.get('url')}", "INFO")
        self.cdp.connect(tab)
        log(f"Viewport size: {self.cdp.viewport_width}x{self.cdp.viewport_height}", "INFO")
        return True

    def run_duel_turn(self):
        """Executes a single turn in an active duel."""
        self.board.turn_number = self.turn_number
        self.board.dismiss_surrender_modal(turn_number=self.turn_number)

        # 1. Action: When board opens for the first time, click cards one by one to get card data,
        # store in variable to perform fusions after having all card info, and print table to console.
        if self.is_board_first_open or self.turn_number == 1:
            log(f"[Turn {self.turn_number}] Board opened for the first time. Inspecting cards one by one...", "DUEL")
            self.cards_in_hand = self.inspect_hand_action.execute(turn_number=self.turn_number)
            self.is_board_first_open = False
        else:
            self.cards_in_hand = self.inspect_hand_action.execute(turn_number=self.turn_number)

        # 2. Action: Fusion - solve hand using strategies and execute fusion after having all cards info in hand
        result = self.fusion_action.solve_hand(self.cards_in_hand)
        sequence, play_name, atk = result
        guardian_star = getattr(result, "guardian_star", None) or self.cfg.guardian_star
        log(f"[Turn {self.turn_number}] Optimal play: {Colors.BOLD}{play_name}{Colors.END} (Est. ATK: {atk})", "FUSION")

        # 3. Action: Execute fusion on board and log name, ATK, and DEF of result
        self.fusion_action.execute(result, turn_number=self.turn_number)
        time.sleep(0.6)

        # 4. Action: Summon & Placement (handles guardian star prompt & field zone placement)
        self.summon_action.execute(
            guardian_star=guardian_star,
            target_zone=0,
            turn_number=self.turn_number,
        )
        time.sleep(self.cfg.turn_wait)
        
        # 5. Action: Execute combat / attacks
        self.attack_action.execute(
            player_zone=2,
            opponent_zone=2,
            turn_number=self.turn_number,
        )

        # 6. Action: End turn
        self.end_turn_action.execute(turn_number=self.turn_number)

        self.turn_number += 1

    def start_farming(self):
        """Starts the autonomous rolling farming loop."""
        if not self.connect_to_chrome():
            return

        self.start_time = time.time()
        self.current_duel_start = time.time()
        self.turn_number = 1
        self.is_board_first_open = True
        self.cards_in_hand = []
        self.inspect_hand_action.reset()

        log(f"Starting auto-dueler against: {Colors.BOLD}{self.cfg.opponent}{Colors.END}", "SUCCESS")
        log(f"Strategy: {self.cfg.strategy} | Guardian Star: {self.cfg.guardian_star}", "INFO")
        log("Press Ctrl+C at any time to pause or stop.", "INFO")
        print("-" * 64)

        consecutive_idle = 0
        try:
            while True:
                state = self.board.detect_screen_state()
                
                if state == GameState.LOBBY:
                    log("Detected Free Duel lobby.", "INFO")
                    self.is_board_first_open = True
                    self.cards_in_hand = []
                    self.inspect_hand_action.reset()
                    self.start_duel_action.execute(self.cfg.opponent, turn_number=self.turn_number)
                    time.sleep(2.0)
                    consecutive_idle = 0

                elif state == GameState.LOADING:
                    log("Connecting to duel...", "INFO")
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.GUARDIAN_STAR:
                    self.board.choose_guardian_star(self.cfg.guardian_star, turn_number=self.turn_number)
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.SURRENDER_PROMPT:
                    log("Detected surrender prompt! Cancelling to prevent forfeit...", "WARN")
                    self.board.dismiss_surrender_modal(turn_number=self.turn_number)
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.CARD_DETAILS:
                    log("Detected Card Details screen in main loop. Selecting FUSION...", "WARN")
                    self.board.select_fusion_on_card_details(turn_number=self.turn_number)
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.IN_DUEL:
                    self.run_duel_turn()
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.VICTORY:
                    self.duels_played += 1
                    self.duels_won += 1
                    duel_duration = time.time() - self.current_duel_start
                    self.current_duel_start = time.time()
                    self.turn_number = 1
                    self.is_board_first_open = True
                    self.cards_in_hand = []
                    self.inspect_hand_action.reset()
                    
                    log(f"{Colors.GREEN}{Colors.BOLD}DUEL #{self.duels_played} WON!{Colors.END} (Duration: {format_duration(duel_duration)})", "SUCCESS")
                    
                    if self.cfg.max_duels > 0 and self.duels_played >= self.cfg.max_duels:
                        log(f"Reached maximum requested duels ({self.cfg.max_duels}). Stopping.", "SUCCESS")
                        break

                    self.lobby.click_duel_again(turn_number=self.turn_number)
                    time.sleep(2.5)
                    consecutive_idle = 0

                elif state == GameState.DEFEAT:
                    self.duels_played += 1
                    self.turn_number = 1
                    self.is_board_first_open = True
                    self.cards_in_hand = []
                    self.inspect_hand_action.reset()

                    log(f"{Colors.RED}Duel defeated.{Colors.END}", "WARN")
                    self.lobby.click_duel_again(turn_number=self.turn_number)
                    time.sleep(2.5)
                    consecutive_idle = 0

                else:
                    consecutive_idle += 1
                    if consecutive_idle % 5 == 0:
                        log("Waiting for game action / animation...", "INFO")
                    time.sleep(1.0)

        except KeyboardInterrupt:
            log("Farming loop paused by user.", "WARN")
        finally:
            self.print_summary()
            self.cdp.close()

    def print_summary(self):
        """Displays total session statistics."""
        total_time = time.time() - self.start_time if self.start_time > 0 else 0
        win_rate = (self.duels_won / self.duels_played * 100) if self.duels_played > 0 else 0.0
        
        print("\n" + "=" * 64)
        print(f"{Colors.CYAN}{Colors.BOLD}                  FARMING SESSION SUMMARY{Colors.END}")
        print("=" * 64)
        print(f" Opponent Farmed:     {Colors.BOLD}{self.cfg.opponent}{Colors.END}")
        print(f" Total Duels:         {self.duels_played}")
        print(f" Victories:           {Colors.GREEN}{self.duels_won}{Colors.END}")
        print(f" Win Rate:            {win_rate:.1f}%")
        print(f" Total Session Time:  {format_duration(total_time)}")
        if self.duels_played > 0:
            avg_time = total_time / self.duels_played
            print(f" Avg Time per Duel:   {format_duration(avg_time)}")
        print("=" * 64 + "\n")
