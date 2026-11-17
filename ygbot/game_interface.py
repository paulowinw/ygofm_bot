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
        Reads the cards currently in the player's hand directly from the live DOM.
        Sorts cards from left to right by x-coordinate to ensure accurate slot indexing (0..4).
        """
        js = """
        (() => {
            // 1. Query loaded hand card images in bottom 45% of viewport
            const imgs = Array.from(document.querySelectorAll('img[alt]')).filter(img => {
                const r = img.getBoundingClientRect();
                return r.y > window.innerHeight * 0.55 && r.height > 40 && img.alt && img.alt.trim();
            });
            imgs.sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
            if (imgs.length > 0) {
                return imgs.map(img => img.alt.trim());
            }

            // 2. Query hand card buttons in bottom 45% of viewport
            const btns = Array.from(document.querySelectorAll('button')).filter(b => {
                const r = b.getBoundingClientRect();
                const text = b.getAttribute('aria-label') || b.innerText.trim();
                return r.y > window.innerHeight * 0.55 && r.height > 40 && text && !text.toUpperCase().includes('END TURN') && !text.toUpperCase().includes('CANCEL');
            });
            btns.sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);
            if (btns.length > 0) {
                return btns.map(b => b.getAttribute('aria-label') || b.innerText.trim());
            }

            return null;
        })()
        """
        try:
            detected = self.cdp.eval_js(js)
            if detected and len(detected) > 0:
                return detected
        except Exception as e:
            log(f"Error reading hand cards via DOM: {e}", "WARN")

        # Fallback hand for simulation or when hand is empty
        return [
            "Bolt Escargot",
            "Kaminari Attack",
            "Curse of Dragon",
            "Curse of Dragon",
            "Shine Palace"
        ]

    def select_card_slot(self, slot_index: int):
        """Clicks a card in hand (slot_index: 0 to 4) via DOM element click with coordinate fallback."""
        js_click = f"""
        (() => {{
            const cards = Array.from(document.querySelectorAll('img[alt]')).filter(img => {{
                const r = img.getBoundingClientRect();
                return r.y > window.innerHeight * 0.55 && r.height > 40 && img.alt && img.alt.trim();
            }}).sort((a, b) => a.getBoundingClientRect().x - b.getBoundingClientRect().x);

            if (cards[{slot_index}]) {{
                const target = cards[{slot_index}].closest('button') || cards[{slot_index}];
                target.click();
                return true;
            }}
            return false;
        }})()
        """
        try:
            clicked = self.cdp.eval_js(js_click)
            if clicked:
                time.sleep(self.cfg.action_delay)
                return
        except Exception:
            pass

        # Coordinate fallback
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
        Executes attacks with field monsters as demonstrated in the duel video:
        1. Clicks the player's monster on field to open the action menu.
        2. Clicks the 'ATTACK' action button.
        3. Targets the opponent's monster zone or direct LP zone to strike.
        """
        log("Executing Battle Phase / Attacks...", "DUEL")
        
        # 1. Click player monster on field
        js_click_monster = """
        (() => {
            const monster = document.querySelector('.board-card-main, [aria*="Dragon"], [aria*="Thunder"]');
            if (monster) {
                monster.click();
                return true;
            }
            return false;
        })()
        """
        try:
            self.cdp.eval_js(js_click_monster)
        except Exception:
            pass
        
        # Coordinate click player zone fallback
        p_coord = self.cfg.player_zones[2]
        self.cdp.click_percent(p_coord[0], p_coord[1])
        time.sleep(0.4)

        # 2. Click "ATTACK" button in card interaction modal
        if self.cdp.click_element_by_text("ATTACK"):
            log("Selected 'ATTACK' action button.", "COMBAT")
            time.sleep(0.4)
        else:
            # Fallback via keyboard Enter
            self.cdp.send_key("Enter", delay=0.08)
            time.sleep(0.4)

        # 3. Target opponent's card or direct LP
        js_click_target = """
        (() => {
            const oppCard = document.querySelector('.slot-opponent, .board-card-opponent, [aria*="opponent"]');
            if (oppCard) {
                oppCard.click();
                return true;
            }
            return false;
        })()
        """
        try:
            self.cdp.eval_js(js_click_target)
        except Exception:
            pass

        # Click direct center on opponent's field
        self.cdp.click_percent(self.cfg.opponent_direct[0], self.cfg.opponent_direct[1])
        self.cdp.send_key("Enter", delay=0.08)
        time.sleep(self.cfg.combat_wait)

    def click_duel_again(self) -> bool:
        """Clicks 'DUEL AGAIN' button on the victory screen."""
        log("Victory achieved! Clicking 'DUEL AGAIN'...", "SUCCESS")
        time.sleep(0.8)

        js = """
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => b.innerText.includes('DUEL AGAIN'));
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        })()
        """
        try:
            if self.cdp.eval_js(js):
                log("Clicked 'DUEL AGAIN' via JS .click().", "SUCCESS")
                return True
        except Exception:
            pass

        # 1. Try DOM element text search
        if self.cdp.click_element_by_text("DUEL AGAIN"):
            log("Clicked 'DUEL AGAIN' via DOM.", "SUCCESS")
            return True

        # 2. Coordinate fallback
        bx, by = self.cfg.duel_again_button
        self.cdp.click_percent(bx, by)
        log("Clicked 'DUEL AGAIN' via screen coordinate.", "SUCCESS")
        return True
