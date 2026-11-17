"""
Autonomous Bot Controller for Forbidden Memories Online.

Manages the rolling farming loop, state machine transitions,
and session statistics using the Adapted Page Object Model.
"""

import time
import sys
from typing import Optional
from .core.config import Config
from .core.cdp_client import CDPClient
from .pages.game_board_page import GameBoardPage, GameState
from .features.cards.card_manager import CardManager
from .features.fusion.engine import FusionEngine
from .core.utils import log, Colors, format_duration


class YGBot:
    """
    Main autonomous duel controller orchestrating the rolling console loop.
    Adheres to Separation of Concerns:
    - Delegates screen interaction to GameBoardPage (Adapted POM).
    - Delegates card parsing to CardManager.
    - Delegates fusion choices to FusionEngine / FusionStrategy.
    """

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config.load()
        self.cdp = CDPClient(host=self.cfg.chrome_host, port=self.cfg.chrome_port)
        self.board = GameBoardPage(self.cdp, self.cfg)
        self.game = self.board  # Backward-compatible alias
        self.cards = CardManager()
        self.fusion = FusionEngine(strategy=self.cfg.strategy)
        
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

        log(f"[Turn {self.turn_number}] Inspecting hand cards...", "DUEL")
        
        # 1. Read hand cards and evaluate via CardManager
        raw_hand = self.board.read_hand_cards()
        hand_models = self.cards.parse_hand(raw_hand)
        log(f"Hand cards: {', '.join(c.name for c in hand_models)}", "INFO")
        
        # 2. Compute best move via FusionEngine & Strategy
        result = self.fusion.solve_hand(hand_models)
        sequence, play_name, atk = result
        guardian_star = getattr(result, "guardian_star", None) or self.cfg.guardian_star
        log(f"[Turn {self.turn_number}] Target play: {Colors.BOLD}{play_name}{Colors.END} (Est. ATK: {atk})", "FUSION")
        log(f"[Turn {self.turn_number}] Playing card sequence: {[i+1 for i in sequence]}", "FUSION")
        
        # 3. Engine requests specific card interactions from GameBoardPage
        self.fusion.execute_fusion(result, board_page=self.board, turn_number=self.turn_number)
        time.sleep(0.6)

        # 4. Check for Guardian Star prompt or Card Details recovery
        state = self.board.detect_screen_state()
        if state == GameState.GUARDIAN_STAR:
            self.board.choose_guardian_star(guardian_star, turn_number=self.turn_number)
            time.sleep(0.5)
        elif state == GameState.CARD_DETAILS:
            log("Still at Card Details screen after fusion sequence. Selecting FUSION to recover...", "WARN")
            self.board.select_fusion_on_card_details(turn_number=self.turn_number)
            time.sleep(0.5)
            return

        # 5. Place monster on field
        if self.board.detect_screen_state() not in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            self.board.place_monster_on_field(target_zone=0, turn_number=self.turn_number)
            time.sleep(self.cfg.turn_wait)
        
        # 6. Execute combat / attacks
        if self.board.detect_screen_state() not in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            self.board.execute_attack(player_zone=2, opponent_zone=2, turn_number=self.turn_number)

        # 7. End turn with 'e' key
        if self.board.detect_screen_state() not in (GameState.SURRENDER_PROMPT,):
            self.board.end_turn(turn_number=self.turn_number)

        self.turn_number += 1

    def start_farming(self):
        """Starts the autonomous rolling farming loop."""
        if not self.connect_to_chrome():
            return

        self.start_time = time.time()
        self.current_duel_start = time.time()
        self.turn_number = 1
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
                    self.board.start_duel_from_lobby(self.cfg.opponent, turn_number=self.turn_number)
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
                    
                    log(f"{Colors.GREEN}{Colors.BOLD}DUEL #{self.duels_played} WON!{Colors.END} (Duration: {format_duration(duel_duration)})", "SUCCESS")
                    
                    if self.cfg.max_duels > 0 and self.duels_played >= self.cfg.max_duels:
                        log(f"Reached maximum requested duels ({self.cfg.max_duels}). Stopping.", "SUCCESS")
                        break

                    self.board.click_duel_again(turn_number=self.turn_number)
                    time.sleep(2.5)
                    consecutive_idle = 0

                elif state == GameState.DEFEAT:
                    self.duels_played += 1
                    self.turn_number = 1
                    log(f"{Colors.RED}Duel defeated.{Colors.END}", "WARN")
                    self.board.click_duel_again(turn_number=self.turn_number)
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
