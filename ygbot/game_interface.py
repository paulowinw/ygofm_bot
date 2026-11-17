"""
High-Level Game Interface for Forbidden Memories Online.
Abstracts DOM inspection and coordinate clicks into game actions.
"""

import time
from typing import Optional, Dict, Any, List, Tuple
from .config import Config
from .cdp_client import CDPClient
from .board_interaction import BoardInteraction
from .utils import log

class GameState:
    UNKNOWN = "UNKNOWN"
    LOBBY = "LOBBY"
    LOADING = "LOADING"
    GUARDIAN_STAR = "GUARDIAN_STAR"
    IN_DUEL = "IN_DUEL"
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"

class GameInterface:
    """Interacts with the web game via CDP Client."""

    def __init__(self, cdp: CDPClient, config: Config):
        self.cdp = cdp
        self.cfg = config
        self.board = BoardInteraction(cdp, config)

    def detect_screen_state(self) -> str:
        """Determines the current state of the game screen."""
        try:
            # Query the page for state indicators
            js = """
            (() => {
                const text = document.body ? document.body.innerText.toUpperCase() : '';
                
                // Check for Victory / Defeat first
                if (text.includes('VICTORY') || text.includes('PREVIEWED CARDS OBTAINED') || text.includes('DUEL AGAIN')) {
                    return 'VICTORY';
                }
                if (text.includes('DEFEAT') || text.includes('YOU LOST')) {
                    return 'DEFEAT';
                }
                
                // Check for Guardian Star Selection Modal
                if (text.includes('CHOOSE A GUARDIAN STAR') || text.includes('GUARDIAN STAR')) {
                    return 'GUARDIAN_STAR';
                }
                
                // Check for Loading
                if (text.includes('CONNECTING TO DUEL') || text.includes('LOADING')) {
                    return 'LOADING';
                }
                
                // Check for Free Duel Lobby
                if (text.includes('FREE DUEL') || text.includes('CAMPAIGN OPPONENTS') || text.includes('START DUEL')) {
                    return 'LOBBY';
                }
                
                // Check for Active Duel (LP counters, hand cards)
                if (text.includes('LP') || text.includes('8000') || text.includes('ATTACK') || text.includes('DEFENSE')) {
                    return 'IN_DUEL';
                }
                
                return 'IN_DUEL';
            })()
            """
            state = self.cdp.eval_js(js)
            if state:
                return state
        except Exception as e:
            log(f"Error detecting state via JS: {e}", "WARN")

        return GameState.IN_DUEL

    def start_duel_from_lobby(self, opponent_name: str) -> bool:
        """Selects opponent and clicks START DUEL."""
        log(f"In Free Duel Lobby. Searching for opponent: {opponent_name}...", "INFO")
        
        # 1. Check if START DUEL button is already visible in drawer
        if self.cdp.click_element_by_text("START DUEL"):
            log("Clicked 'START DUEL' button.", "SUCCESS")
            return True

        # 2. Search or click opponent card
        clicked_opp = self.cdp.click_element_by_text(opponent_name)
        if not clicked_opp:
            # Fallback: type opponent name in search bar or click search
            js_search = f"""
            (() => {{
                const input = document.querySelector('input[type="text"], input[placeholder*="Search"]');
                if (input) {{
                    input.value = '{opponent_name}';
                    input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                    input.dispatchEvent(new Event('change', {{ bubbles: true }}));
                    return true;
                }}
                return false;
            }})()
            """
            self.cdp.eval_js(js_search)
            time.sleep(0.5)
            self.cdp.click_element_by_text(opponent_name)

        time.sleep(0.6)
        
        # 3. Click START DUEL button
        if self.cdp.click_element_by_text("START DUEL"):
            log("Clicked 'START DUEL' button.", "SUCCESS")
            return True

        # Coordinate fallback for START DUEL
        log("Trying coordinate fallback for 'START DUEL'...", "INFO")
        bx, by = self.cfg.start_duel_button
        self.cdp.click_percent(bx, by)
        return True

    def read_hand_cards(self) -> List[str]:
        """
        Attempts to read cards currently in the player's hand via DOM.
        If cards cannot be extracted from DOM (e.g. WebGL Canvas), returns
        heuristic deck cards that prioritize the user's THTD strategy.
        """
        js = """
        (() => {
            // Check for card elements with aria-label, title, or text
            const cardNodes = Array.from(document.querySelectorAll('[data-card-name], .card-name, .hand-card, [title]'));
            if (cardNodes.length >= 5) {
                return cardNodes.slice(0, 5).map(c => c.getAttribute('data-card-name') || c.getAttribute('title') || c.innerText.trim());
            }
            return null;
        })()
        """
        try:
            detected = self.cdp.eval_js(js)
            if detected and len(detected) == 5:
                return detected
        except Exception:
            pass

        # Return classic THTD-oriented hand as default for FM farming
        # (Thunder monster, Dragon monsters, Equips)
        return [
            "Bolt Escargot",
            "Kaminari Attack",
            "Curse of Dragon",
            "Curse of Dragon",
            "Shine Palace"
        ]

    def select_card_slot(self, slot_index: int):
        """Clicks a card in hand (slot_index: 0 to 4)."""
        if 0 <= slot_index < len(self.cfg.hand_cards):
            coords = self.cfg.hand_cards[slot_index]
            self.cdp.click_percent(coords[0], coords[1])
            time.sleep(self.cfg.action_delay)

    def choose_guardian_star(self, preferred: str = "Pluto") -> bool:
        """Selects guardian star when modal appears using keyboard '1' or '2' with mouse fallback."""
        log(f"Guardian Star prompt: selecting '{preferred}'...", "INFO")
        time.sleep(0.4)
        
        # 1. Primary: Use BoardInteraction keyboard shortcut ('1' for 1st option, '2' for 2nd)
        self.board.choose_guardian_star(preferred)
        time.sleep(0.3)

        # 2. Try DOM element fallback if modal remains
        if self.cdp.click_element_by_text(preferred):
            log(f"Selected Guardian Star via DOM: {preferred}", "SUCCESS")
            return True

        # 3. Coordinate fallback (Pluto: left button, Mercury: right button)
        coords = self.cfg.guardian_star_coords.get(preferred, self.cfg.guardian_star_coords["Pluto"])
        self.cdp.click_percent(coords[0], coords[1])
        return True

    def confirm_monster_placement(self, preferred_zone: int = 2):
        """Places monster on field zone using keyboard navigation and Enter."""
        time.sleep(0.3)
        self.board.place_monster_on_field(preferred_zone)
        # Coordinate fallback to ensure placement
        if 0 <= preferred_zone < len(self.cfg.player_zones):
            coords = self.cfg.player_zones[preferred_zone]
            self.cdp.click_percent(coords[0], coords[1])

    def perform_attack_sequence(self):
        """
        Executes attacks with field monsters against opponent.
        Iterates across player monster zones and targets opponent zones / direct attack.
        """
        log("Executing Battle Phase / Attacks...", "DUEL")
        
        # Check if combat button is available and click it
        self.cdp.click_element_by_text("COMBAT")
        bx, by = self.cfg.combat_button
        self.cdp.click_percent(bx, by)
        time.sleep(0.4)

        # Attack with player's active monster zones (Zones 1, 2, 3)
        for zone_idx in [1, 2, 3, 0, 4]:
            p_coord = self.cfg.player_zones[zone_idx]
            # Click player monster
            self.cdp.click_percent(p_coord[0], p_coord[1], delay=0.08)
            time.sleep(0.2)
            
            # Click opponent target (Opponent monster zone 1-3 or direct attack)
            o_coord = self.cfg.opponent_zones[zone_idx] if zone_idx < len(self.cfg.opponent_zones) else self.cfg.opponent_direct
            self.cdp.click_percent(o_coord[0], o_coord[1], delay=0.08)
            time.sleep(0.3)
            
            # Also click opponent direct center to ensure hit connects
            self.cdp.click_percent(self.cfg.opponent_direct[0], self.cfg.opponent_direct[1], delay=0.08)
            time.sleep(0.2)

        time.sleep(self.cfg.combat_wait)

    def click_duel_again(self) -> bool:
        """Clicks 'DUEL AGAIN' button on the victory screen."""
        log("Victory achieved! Clicking 'DUEL AGAIN'...", "SUCCESS")
        time.sleep(0.8)

        # 1. Try DOM element
        if self.cdp.click_element_by_text("DUEL AGAIN"):
            log("Clicked 'DUEL AGAIN' via DOM.", "SUCCESS")
            return True

        # 2. Coordinate fallback
        bx, by = self.cfg.duel_again_button
        self.cdp.click_percent(bx, by)
        log("Clicked 'DUEL AGAIN' via screen coordinate.", "SUCCESS")
        return True
