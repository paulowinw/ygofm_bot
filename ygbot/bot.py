"""
Autonomous Bot Controller for Forbidden Memories Online.
Manages the farming loop, state machine transitions, and session statistics.
"""

import time
import sys
from typing import Optional
from .config import Config
from .cdp_client import CDPClient
from .game_interface import GameInterface, GameState
from .fusion_engine import FusionEngine
from .utils import log, Colors, format_duration

class YGBot:
    """Main autonomous duel controller."""

    def __init__(self, config: Optional[Config] = None):
        self.cfg = config or Config.load()
        self.cdp = CDPClient(host=self.cfg.chrome_host, port=self.cfg.chrome_port)
        self.game = GameInterface(self.cdp, self.cfg)
        self.fusion = FusionEngine(strategy=self.cfg.strategy)
        
        # Stats
        self.duels_played = 0
        self.duels_won = 0
        self.start_time = 0.0
        self.current_duel_start = 0.0

    def connect_to_chrome(self) -> bool:
        """Verifies Chrome is running with remote debugging and attaches to game tab."""
        log(f"Checking Google Chrome on {self.cfg.chrome_host}:{self.cfg.chrome_port}...", "INFO")
        
        if not self.cdp.is_chrome_running():
            log(f"Could not connect to Chrome on port {self.cfg.chrome_port}.", "ERROR")
            log(f"Please launch Google Chrome with remote debugging enabled:", "WARN")
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
        # 0. Safety: dismiss any surrender modal if accidentally opened
        self.game.dismiss_surrender_modal()

        log("Turn active. Inspecting hand cards...", "DUEL")
        
        # 1. Read hand cards
        hand = self.game.read_hand_cards()
        log(f"Hand cards: {', '.join(hand)}", "INFO")
        
        # 2. Compute best play
        result = self.fusion.solve_hand(hand)
        sequence, play_name, atk = result
        guardian_star = getattr(result, "guardian_star", None) or self.cfg.guardian_star
        log(f"Target play: {Colors.BOLD}{play_name}{Colors.END} (Est. ATK: {atk})", "FUSION")
        log(f"Playing card sequence: {[i+1 for i in sequence]}", "FUSION")
        
        # 3. Execute keyboard/DOM fusion sequence on the board
        self.game.board.execute_fusion_sequence(sequence)
        time.sleep(0.6)

        # 4. Check for Guardian Star prompt or Card Details recovery
        state = self.game.detect_screen_state()
        if state == GameState.GUARDIAN_STAR:
            # Select appropriate guardian star ('Sun' for Meteor Black Dragon, 'Pluto' for THTD)
            self.game.choose_guardian_star(guardian_star)
            time.sleep(0.5)
        elif state == GameState.CARD_DETAILS:
            log("Still at Card Details screen after fusion sequence. Selecting FUSION to recover...", "WARN")
            self.game.select_fusion_on_card_details()
            time.sleep(0.5)
            return

        # 5. Place monster on field (preferred zone 0 as seen in video)
        if self.game.detect_screen_state() not in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            self.game.confirm_monster_placement(preferred_zone=0)
            time.sleep(self.cfg.turn_wait)
        
        # 6. Execute combat / attacks
        if self.game.detect_screen_state() not in (GameState.CARD_DETAILS, GameState.SURRENDER_PROMPT):
            self.game.perform_attack_sequence()

        # 7. End turn with 'e' key
        if self.game.detect_screen_state() not in (GameState.SURRENDER_PROMPT,):
            self.game.board.end_turn()

    def start_farming(self):
        """Starts the autonomous farming loop."""
        if not self.connect_to_chrome():
            return

        self.start_time = time.time()
        self.current_duel_start = time.time()
        log(f"Starting auto-dueler against: {Colors.BOLD}{self.cfg.opponent}{Colors.END}", "SUCCESS")
        log(f"Strategy: {self.cfg.strategy} | Guardian Star: {self.cfg.guardian_star}", "INFO")
        log("Press Ctrl+C at any time to pause or stop.", "INFO")
        print("-" * 64)

        consecutive_idle = 0
        try:
            while True:
                state = self.game.detect_screen_state()
                
                if state == GameState.LOBBY:
                    log("Detected Free Duel lobby.", "INFO")
                    self.game.start_duel_from_lobby(self.cfg.opponent)
                    time.sleep(2.0)
                    consecutive_idle = 0

                elif state == GameState.LOADING:
                    log("Connecting to duel...", "INFO")
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.GUARDIAN_STAR:
                    self.game.choose_guardian_star(self.cfg.guardian_star)
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.SURRENDER_PROMPT:
                    log("Detected surrender prompt! Cancelling to prevent forfeit...", "WARN")
                    self.game.dismiss_surrender_modal()
                    time.sleep(1.0)
                    consecutive_idle = 0

                elif state == GameState.CARD_DETAILS:
                    log("Detected Card Details screen in main loop. Selecting FUSION...", "WARN")
                    self.game.select_fusion_on_card_details()
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
                    
                    log(f"{Colors.GREEN}{Colors.BOLD}DUEL #{self.duels_played} WON!{Colors.END} (Duration: {format_duration(duel_duration)})", "SUCCESS")
                    
                    if self.cfg.max_duels > 0 and self.duels_played >= self.cfg.max_duels:
                        log(f"Reached maximum requested duels ({self.cfg.max_duels}). Stopping.", "SUCCESS")
                        break

                    self.game.click_duel_again()
                    time.sleep(2.5)
                    consecutive_idle = 0

                elif state == GameState.DEFEAT:
                    self.duels_played += 1
                    log(f"{Colors.RED}Duel defeated.{Colors.END}", "WARN")
                    self.game.click_duel_again()
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
