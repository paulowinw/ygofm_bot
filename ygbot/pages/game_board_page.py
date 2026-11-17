"""
Game Board Page Object for Yu-Gi-Oh! Forbidden Memories Arena.

Adapted Page Object Model (POM):
Encapsulates screen layout, selectors, canvas/DOM element locations,
and user interaction sequences for the game arena.
"""

import time
from typing import List, Optional, Tuple, Dict, Any, Union
from .base_page import BasePage
from ..core.utils import log, Colors


class GameState:
    """Enumeration of recognizable game screen states."""
    UNKNOWN = "UNKNOWN"
    LOBBY = "LOBBY"
    LOADING = "LOADING"
    CARD_DETAILS = "CARD_DETAILS"
    SURRENDER_PROMPT = "SURRENDER_PROMPT"
    GUARDIAN_STAR = "GUARDIAN_STAR"
    IN_DUEL = "IN_DUEL"
    VICTORY = "VICTORY"
    DEFEAT = "DEFEAT"


class GameBoardPage(BasePage):
    """
    Page Object representing the Forbidden Memories duel arena, hand slots,
    field zones, and interactive modals.
    """

    def __init__(self, cdp, config=None, pipeline=None, vision=None):
        super().__init__(cdp=cdp, config=config, pipeline=pipeline, vision=vision)
        self.current_hand_slot: Optional[int] = None
        self.current_field_zone: int = 2
        self.turn_number: int = 1
        self.key_delay: float = getattr(self.cfg, "action_delay", 0.35)

    def detect_screen_state(self) -> str:
        """Determines current screen state using DOM text & element inspection."""
        js = """
        (() => {
            const text = document.body ? document.body.innerText.toUpperCase() : '';
            if (text.includes('VICTORY') || text.includes('PREVIEWED CARDS OBTAINED') || text.includes('DUEL AGAIN')) {
                return 'VICTORY';
            }
            if (text.includes('DEFEAT') || text.includes('YOU LOST')) {
                return 'DEFEAT';
            }
            if (text.includes('CONCEDE THIS MATCH NOW') || text.includes('SURRENDERED MATCHES GRANT NO REWARD')) {
                return 'SURRENDER_PROMPT';
            }
            const hasActionGroup = !!document.querySelector('.desktop-duel-action-group, [data-testid="summon-chain"], .desktop-duel-action--green');
            const hasAtkDef = document.querySelectorAll('[data-testid="summon-atk"], [data-testid="summon-def-faceup"]').length > 0;
            if (hasActionGroup || hasAtkDef) {
                return 'CARD_DETAILS';
            }
            if (text.includes('CHOOSE A GUARDIAN STAR') || text.includes('GUARDIAN STAR')) {
                return 'GUARDIAN_STAR';
            }
            if (text.includes('CONNECTING TO DUEL') || text.includes('LOADING')) {
                return 'LOADING';
            }
            if (text.includes('FREE DUEL') || text.includes('CAMPAIGN OPPONENTS') || text.includes('START DUEL')) {
                return 'LOBBY';
            }
            return 'IN_DUEL';
        })()
        """
        try:
            state = self.eval_js(js, description="Detect screen state", turn_number=self.turn_number)
            return state or GameState.IN_DUEL
        except Exception:
            return GameState.IN_DUEL

    def read_hand_cards(self) -> List[str]:
        """Reads card names from the player's 5 hand slots."""
        js = """
        (() => {
            const cards = [];
            const elements = document.querySelectorAll('[data-card-name], .hand-card, [data-testid^="hand-slot-"], .duel-card');
            for (const el of elements) {
                const name = el.getAttribute('data-card-name') || el.getAttribute('title') || el.innerText;
                if (name && name.trim()) cards.push(name.trim());
            }
            return cards.slice(0, 5);
        })()
        """
        try:
            cards = self.eval_js(js, description="Read hand cards", turn_number=self.turn_number)
            if cards and isinstance(cards, list) and len(cards) > 0:
                return cards
        except Exception:
            pass
        return ["Curse of Dragon", "Bolt Escargot", "Dragon Treasure", "Baby Dragon", "Kaminari Attack"]

    def get_card_coordinates(self, slot_index: int) -> Tuple[float, float]:
        """Returns normalized (x, y) coordinates for a given hand slot (0..4)."""
        hand_coords = getattr(self.cfg, "hand_cards", [])
        if 0 <= slot_index < len(hand_coords):
            c = hand_coords[slot_index]
            return float(c[0]), float(c[1])
        x_offsets = [0.372, 0.417, 0.461, 0.505, 0.550]
        idx = max(0, min(slot_index, len(x_offsets) - 1))
        return x_offsets[idx], 0.870

    def click_hand_card(self, slot_index: int, turn_number: Optional[int] = None) -> bool:
        """Clicks the hand card directly in DOM to raise/lift it or open details."""
        t = turn_number or self.turn_number
        js = f"""
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
            return bool(self.eval_js(js, description=f"DOM click hand card {slot_index}", turn_number=t))
        except Exception:
            return False

    def open_card_details(self, turn_number: Optional[int] = None) -> bool:
        """Opens the card details box/modal for the focused card with Enter."""
        t = turn_number or self.turn_number
        self.send_key("Enter", description="Show card info [Enter]", turn_number=t)
        time.sleep(self.key_delay)
        return True

    def close_card_details(self, turn_number: Optional[int] = None) -> bool:
        """Closes the opened card details box with Escape (Esc)."""
        t = turn_number or self.turn_number
        self.send_key("Escape", description="Close card box [Esc]", turn_number=t)
        time.sleep(self.key_delay)
        return True

    def focus_next_hand_card(self, turn_number: Optional[int] = None) -> bool:
        """Focuses the next hand card by pressing ArrowRight."""
        t = turn_number or self.turn_number
        self.send_key("ArrowRight", description="Focus next card -> [ArrowRight]", turn_number=t)
        if self.current_hand_slot is not None:
            self.current_hand_slot = min(self.current_hand_slot + 1, 4)
        else:
            self.current_hand_slot = 0
        time.sleep(self.key_delay)
        return True

    def read_opened_card_details(self, slot_index: int = 0, turn_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Extracts optimal card details (name, ATK, DEF, type, star) from the currently opened card details box in the DOM.
        """
        t = turn_number or self.turn_number
        js_inspect = f"""
        (() => {{
            const modal = document.querySelector(
                '.card-detail, [role="dialog"], .desktop-duel-action-group, ' +
                '.card-modal, .card-info-box, [data-testid="card-detail-modal"], .duel-card-details'
            ) || document.body;

            const titleEl = modal.querySelector(
                '.card-detail-title, [data-testid="card-title"], [data-testid="card-detail-name"], ' +
                '.card-name, .modal-title, h1, h2, h3, [data-card-name]'
            );
            const atkEl = modal.querySelector(
                '[data-testid="summon-atk"], .card-stat-atk, [data-testid="card-detail-atk"], .atk'
            );
            const defEl = modal.querySelector(
                '[data-testid="summon-def-faceup"], [data-testid="summon-def"], .card-stat-def, ' +
                '[data-testid="card-detail-def"], .def'
            );
            const typeEl = modal.querySelector(
                '[data-testid="card-type"], .card-type, [data-testid="card-detail-type"], .type'
            );
            const starEl = modal.querySelector(
                '[data-testid="guardian-star"], .guardian-star, [data-testid="card-detail-star"], .star'
            );

            let name = titleEl ? titleEl.innerText.trim() : null;
            let atk = atkEl ? parseInt(atkEl.innerText.replace(/\\D/g, '')) || null : null;
            let def_ = defEl ? parseInt(defEl.innerText.replace(/\\D/g, '')) || null : null;
            let type = typeEl ? typeEl.innerText.trim() : null;
            let star = starEl ? starEl.innerText.trim() : null;

            const modalText = modal.innerText || '';
            if (atk === null) {{
                const atkMatch = modalText.match(/ATK\\s*[:\\/\\s]*(\\d+)/i);
                if (atkMatch) atk = parseInt(atkMatch[1]);
            }}
            if (def_ === null) {{
                const defMatch = modalText.match(/DEF\\s*[:\\/\\s]*(\\d+)/i);
                if (defMatch) def_ = parseInt(defMatch[1]);
            }}
            if (!type) {{
                const typeMatch = modalText.match(/(Dragon|Thunder|Equip|Spell|Spellcaster|Aqua|Sea Serpent|Pyro|Beast|Plant|Rock|Female|Warrior|Zombie|Machine|Fiend)/i);
                if (typeMatch) type = typeMatch[1];
            }}
            if (!star) {{
                const starMatch = modalText.match(/(Sun|Moon|Mercury|Venus|Mars|Jupiter|Saturn|Uranus|Pluto|Neptune)/i);
                if (starMatch) star = starMatch[1];
            }}

            if (!name && modalText) {{
                const lines = modalText.split('\\n').map(l => l.trim()).filter(l => l.length > 0);
                for (const line of lines) {{
                    const u = line.toUpperCase();
                    if (!u.includes('ATK') && !u.includes('DEF') && !u.includes('FUSION') &&
                        !u.includes('ATTACK') && !u.includes('DEFENSE') && !u.includes('CONCEDE') &&
                        !u.includes('DUEL') && line.length > 2 && line.length < 35) {{
                        name = line;
                        break;
                    }}
                }}
            }}

            return {{
                "name": name,
                "atk": atk,
                "def": def_,
                "type": type,
                "star": star,
            }};
        }})()
        """
        data = None
        try:
            data = self.eval_js(js_inspect, description=f"Read opened card details (slot {slot_index})", turn_number=t)
        except Exception:
            pass

        if not data or not data.get("name"):
            names = self.read_hand_cards()
            card_name = names[slot_index] if slot_index < len(names) else f"Card {slot_index + 1}"
            data = {"name": card_name, "atk": None, "def": None, "type": None, "star": None}

        return data

    def inspect_card_at_slot(self, slot_index: int, turn_number: Optional[int] = None) -> Dict[str, Any]:
        """
        Navigates to card slot, opens card box with Enter, extracts optimal details, and closes with Esc.
        """
        t = turn_number or self.turn_number
        if self.current_hand_slot != slot_index:
            self.navigate_to_hand_slot(slot_index, turn_number=t)
        self.open_card_details(turn_number=t)
        data = self.read_opened_card_details(slot_index=slot_index, turn_number=t)
        self.close_card_details(turn_number=t)
        return data

    def click_card_at_slot(self, slot_index: int, turn_number: Optional[int] = None) -> bool:
        """Clicks the card image at the given hand slot through DOM or coordinates."""
        t = turn_number or self.turn_number
        if self.click_hand_card(slot_index, turn_number=t):
            return True
        x, y = self.get_card_coordinates(slot_index)
        selector = f'[data-testid="hand-slot-{slot_index}"]'
        return self.click(
            x=x,
            y=y,
            selector=selector,
            fallback_coords=(x, y),
            description=f"Select Card at Slot {slot_index}",
            turn_number=t,
        )

    def focus_hand(self, turn_number: Optional[int] = None):
        """Moves initial cursor focus to the 1st card in hand (slot 0)."""
        t = turn_number or self.turn_number
        self.send_key("ArrowDown", description="Focus hand [ArrowDown]", turn_number=t)
        self.current_hand_slot = 0

    def navigate_to_hand_slot(self, target_slot: int, turn_number: Optional[int] = None):
        """Navigates cursor across hand slots (0..4) using Arrow keys."""
        t = turn_number or self.turn_number
        if self.current_hand_slot is None:
            self.focus_hand(turn_number=t)

        delta = target_slot - (self.current_hand_slot or 0)
        if delta > 0:
            for _ in range(delta):
                self.send_key("ArrowRight", description="Hand cursor -> [ArrowRight]", turn_number=t)
        elif delta < 0:
            for _ in range(abs(delta)):
                self.send_key("ArrowLeft", description="Hand cursor <- [ArrowLeft]", turn_number=t)

        self.current_hand_slot = target_slot

    def lift_card_for_fusion(self, turn_number: Optional[int] = None):
        """Lifts focused card into fusion queue using ArrowUp."""
        t = turn_number or self.turn_number
        self.send_key("ArrowUp", description=f"Lift card at slot {self.current_hand_slot} [ArrowUp]", turn_number=t)

    def trigger_fusion(self, turn_number: Optional[int] = None) -> bool:
        """Triggers the fusion animation and calculation."""
        t = turn_number or self.turn_number
        self.send_key("Enter", description="Trigger fusion [Enter]", turn_number=t)
        self.current_hand_slot = None
        return True

    def select_fusion_on_card_details(self, turn_number: Optional[int] = None) -> bool:
        """Selects FUSION button when Card Details modal is open."""
        t = turn_number or self.turn_number
        self.send_key("ArrowDown", description="Card details: move to FUSION [ArrowDown]", turn_number=t)
        self.send_key("Enter", description="Confirm fusion on card details [Enter]", turn_number=t)
        
        js = """
        (() => {
            const btn = document.querySelector('[data-testid="summon-chain"], .desktop-duel-action--green, button.fusion-btn');
            if (btn) { btn.click(); return true; }
            return false;
        })()
        """
        self.eval_js(js, description="DOM click FUSION button", turn_number=t)
        return True

    def is_card_details_open(self) -> bool:
        """Verifies if card details screen is currently open."""
        js_check = """
        (() => {
            const hasActionGroup = !!document.querySelector('.desktop-duel-action-group, [data-testid="summon-chain"], .desktop-duel-action--green');
            const hasActions = document.querySelectorAll('.desktop-duel-action, [data-testid^="summon-"]').length > 0;
            const hasModal = !!document.querySelector('.card-detail, [role="dialog"]:not([data-testid="zone-selector"])');
            return hasActionGroup || hasActions || hasModal;
        })()
        """
        try:
            return bool(self.eval_js(js_check, description="Check if card details open"))
        except Exception:
            return False

    def is_fusion_selected_on_card_details(self) -> bool:
        """Checks if fusion option is active on card details screen."""
        js = """
        (() => {
            const badges = document.querySelectorAll('.hand-card-quick-fusion-mark, [data-testid="memories-effect-badge"], .hand-card-quick-btn--fusion, [data-gamepad-fusion-confirm], [data-testid="memories-fusion-hand-controls"]');
            if (badges.length > 0) return true;
            const chainBtn = document.querySelector('[data-testid="summon-chain"]');
            return chainBtn !== null;
        })()
        """
        try:
            return bool(self.eval_js(js, description="Check if fusion selected"))
        except Exception:
            return False

    def execute_fusion_sequence(self, sequence: List[int], turn_number: Optional[int] = None) -> bool:
        """
        Executes sequence of navigation and clicks for fusion.
        Sequence: for each card index, focus/navigate, select fusion on card details, then trigger fusion.
        """
        if not sequence:
            log("Empty sequence provided, skipping fusion.", "WARN")
            return False

        t = turn_number or self.turn_number
        log(f"Executing fusion sequence: {[idx + 1 for idx in sequence]}", "FUSION")
        self.dismiss_surrender_modal(turn_number=t)
        self.focus_hand(turn_number=t)

        for card_idx in sequence:
            self.navigate_to_hand_slot(card_idx, turn_number=t)
            self.click_hand_card(card_idx)
            self.select_fusion_on_card_details(turn_number=t)

        if self.key_delay > 0:
            time.sleep(self.key_delay * 0.8)

        self.trigger_fusion(turn_number=t)
        return True

    def place_monster_on_field(self, target_zone: int = 2, turn_number: Optional[int] = None) -> None:
        """Selects field zone (0..4) and confirms monster placement."""
        t = turn_number or self.turn_number
        target_zone = max(0, min(4, target_zone))
        log(f"Selecting field zone {target_zone} for monster placement...", "DUEL")

        js_zone = f"""
        (() => {{
            const zoneBtn = document.querySelector('[data-testid="zone-selector-{target_zone}"], [data-zone-index="{target_zone}"]');
            if (zoneBtn) {{
                zoneBtn.click();
                return true;
            }}
            return false;
        }})()
        """
        clicked = False
        try:
            clicked = bool(self.eval_js(js_zone, description=f"Click field zone {target_zone}", turn_number=t))
        except Exception:
            pass

        delta = target_zone - self.current_field_zone
        if delta > 0:
            for _ in range(delta):
                self.send_key("ArrowRight", description="Zone cursor -> [ArrowRight]", turn_number=t)
        elif delta < 0:
            for _ in range(abs(delta)):
                self.send_key("ArrowLeft", description="Zone cursor <- [ArrowLeft]", turn_number=t)

        self.current_field_zone = target_zone
        self.send_key("Enter", description=f"Confirmed placement on zone {target_zone} [Enter]", turn_number=t)
        log(f"Confirmed placement on zone {target_zone} [Enter].", "SUCCESS")

    def choose_guardian_star(self, choice: Union[str, int] = "Pluto", turn_number: Optional[int] = None) -> None:
        """Selects Guardian Star option ('1' for Primary, '2' for Secondary)."""
        t = turn_number or self.turn_number
        is_second = str(choice).lower() in ("mercury", "neptune", "moon", "2", "right")
        key = "2" if is_second else "1"
        log(f"Selecting Guardian Star option '{key}' via keyboard...", "INFO")
        self.send_key(key, description=f"Guardian Star option '{key}'", turn_number=t)

    def select_guardian_star(self, choice: Union[str, int] = "Pluto", turn_number: Optional[int] = None) -> None:
        """Alias for choose_guardian_star."""
        self.choose_guardian_star(choice, turn_number=turn_number)

    def dismiss_surrender_modal(self, turn_number: Optional[int] = None) -> bool:
        """Dismisses accidental surrender modal."""
        t = turn_number or self.turn_number
        js_cancel = """
        (() => {
            const btns = Array.from(document.querySelectorAll('button'));
            const cancelBtn = btns.find(b => {
                const txt = (b.innerText || '').trim().toLowerCase();
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                return (txt === 'cancel' || aria === 'cancel' || b.hasAttribute('data-gamepad-cancel')) && !txt.includes('concede');
            });
            if (cancelBtn) {
                cancelBtn.click();
                return true;
            }
            return false;
        })()
        """
        try:
            if self.eval_js(js_cancel, description="Check cancel surrender prompt", turn_number=t):
                log("Accidental surrender prompt detected and cancelled!", "WARN")
                return True
        except Exception:
            pass
        return False

    def execute_attack(self, player_zone: int = 2, opponent_zone: int = 2, turn_number: Optional[int] = None) -> bool:
        """Executes attack from player_zone to opponent_zone."""
        t = turn_number or self.turn_number
        if self.is_card_details_open():
            log("Card details open, skipping attack sequence.", "WARN")
            return False

        log(f"Initiating attack from zone {player_zone} to opponent zone {opponent_zone}...", "COMBAT")
        self.send_key("Enter", description="Open card interaction [Enter]", turn_number=t)
        self.send_key("Enter", description="Confirm Attack command [Enter]", turn_number=t)
        self.send_key("Enter", description="Confirm attack target [Enter]", turn_number=t)
        log("Attack executed [Enter].", "SUCCESS")
        return True

    def perform_attack_sequence(self, player_zone: int = 2, opponent_zone: int = 2, turn_number: Optional[int] = None) -> bool:
        """Semantic alias for execute_attack."""
        return self.execute_attack(player_zone=player_zone, opponent_zone=opponent_zone, turn_number=turn_number)

    def confirm_monster_placement(self, preferred_zone: int = 0, turn_number: Optional[int] = None) -> None:
        """Semantic alias for place_monster_on_field."""
        self.place_monster_on_field(target_zone=preferred_zone, turn_number=turn_number)

    def end_turn(self, turn_number: Optional[int] = None) -> bool:
        """Ends player turn with 'e' key."""
        t = turn_number or self.turn_number
        log("Ending turn: clicking 'End turn' / pressing ['e']...", "DUEL")
        self.send_key("e", description="End turn ['e']", turn_number=t)
        self.current_hand_slot = None
        return True

    def start_duel_from_lobby(self, opponent_name: str, turn_number: Optional[int] = None) -> bool:
        """Selects opponent and clicks START DUEL in Free Duel lobby."""
        t = turn_number or self.turn_number
        if self.click(text="START DUEL", description="Click 'START DUEL'", turn_number=t):
            return True
        return self.click(text=opponent_name, description=f"Select Opponent '{opponent_name}'", turn_number=t)

    def click_duel_again(self, turn_number: Optional[int] = None) -> bool:
        """Clicks DUEL AGAIN button on victory/defeat screen."""
        t = turn_number or self.turn_number
        bx, by = getattr(self.cfg, "duel_again_button", [0.448, 0.588])
        if self.click(text="DUEL AGAIN", description="Click 'DUEL AGAIN' button", turn_number=t):
            return True
        return self.click(x=bx, y=by, description="Click DUEL AGAIN by coordinate", turn_number=t)
