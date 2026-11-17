"""
Board Interaction Controller for Yu-Gi-Oh! Forbidden Memories Online.

Design Pattern: Controller & Command Pattern
---------------------------------------------
1. Controller Pattern (GRASP / MVC):
   - `BoardInteraction` acts as the Board Controller.
   - Decouples high-level bot orchestration (`YGBot` / `GameInterface`) from the physical
     keyboard protocol and discrete board cursor positions.
   - Tracks cursor state (focused hand slot, field zone) and translates high-level game
     intents (e.g. "fuse cards [0, 2]", "attack zone 2", "end turn") into precise keyboard inputs.

2. Command Pattern:
   - Each tactical board operation (`focus_hand`, `navigate_to_card`, `lift_card_for_fusion`,
     `trigger_fusion`, `select_guardian_star`, `place_monster`, `attack_target`, `end_turn`)
     is implemented as a discrete command sequence with parameterized timing and safety verification.

====================================================================================================
KEYBOARD NAVIGATION & BOARD INTERACTION REFERENCE (Forbidden Memories Online)
====================================================================================================
1. Hand Activation & Focus:
   - At the beginning of a duel turn, the board has no active card focus.
   - Pressing [ArrowDown] moves the cursor focus directly to the first card in hand (Slot 0).

2. Hand Navigation:
   - Once focus is in hand, pressing [ArrowLeft] moves focus to the card to the left.
   - Pressing [ArrowRight] moves focus to the card to the right.
   - Hand slots are indexed from 0 to 4 (left to right, 5 cards max).

3. Card Selection & Fusion Queue ("Upping" Cards):
   - When a card is focused in hand, pressing [ArrowUp] "lifts" the card up into the fusion queue.
   - Multiple cards can be lifted in sequence to create a fusion chain.
   - Pressing [ArrowDown] from a hand card navigates down towards the fusion button.

4. Starting the Fusion:
   - After lifting all desired fusion materials into the fusion queue, pressing [Enter]
     initiates the fusion sequence.

5. Field Zone Selection & Monster Placement:
   - After confirming fusion or normal summon, field zone selection is activated.
   - Use [ArrowLeft] and [ArrowRight] to navigate across the 5 player monster zones (Zone 0 to 4).
   - Pressing [Enter] confirms monster placement on the highlighted field zone.

6. Guardian Star Selection Modal:
   - When the Guardian Star modal appears:
     * Press ['1'] to select the 1st option (Primary Guardian Star, e.g. Pluto / Mars / Sun).
     * Press ['2'] to select the 2nd option (Secondary Guardian Star, e.g. Mercury / Neptune / Moon).

7. Combat & Attacking:
   - Focus on a summoned monster on the field using arrow keys.
   - Press [Enter] to open the card interaction menu (Attack / Defend).
   - Press [Enter] again to select "Attack".
   - Navigate across the opponent's field zones using [ArrowLeft] / [ArrowRight] to target
     an enemy monster or direct LP.
   - Press [Enter] to execute the attack!

8. Ending Turn:
   - To end the player's turn at any time during the combat/main phase, press ['e'] or ['E'].

9. Confirming Any Action:
   - Press [Enter] to confirm selections and close dialogs.
====================================================================================================
"""

import time
from typing import List, Optional, Union
from .cdp_client import CDPClient
from .config import Config
from .utils import log, Colors


class BoardInteraction:
    """
    Controller responsible for all board navigation and keyboard-driven actions
    in Forbidden Memories Online.
    """

    def __init__(self, cdp: CDPClient, config: Optional[Config] = None):
        """
        Initializes the board interaction controller.
        
        Args:
            cdp: The active Chrome DevTools Protocol client.
            config: Bot configuration parameters (key delays, guardian star preference, etc.).
        """
        self.cdp = cdp
        self.cfg = config or Config.load()
        
        # Cursor state tracking
        self.current_hand_slot: Optional[int] = None
        self.current_field_zone: int = 2  # Default middle zone (index 2: 0..4)
        self.key_delay: float = getattr(self.cfg, "action_delay", 0.35)

    def _press_key(self, key_name: str, delay_mult: float = 1.0):
        """Dispatches a single key event and pauses for scaled action delay."""
        d = self.key_delay * delay_mult
        self.cdp.send_key(key_name, delay=0.04 if d > 0 else 0.0)
        if d > 0:
            time.sleep(d)

    # =========================================================================
    # 1. Hand Navigation & Fusion
    # =========================================================================

    def focus_hand(self) -> None:
        """
        Activates the hand at the start of a turn.
        Presses [ArrowDown] to move the initial focus to the first card in hand (slot 0).
        """
        log("Focusing hand: pressing [ArrowDown]...", "DUEL")
        self._press_key("ArrowDown", delay_mult=1.0)
        self.current_hand_slot = 0

    def navigate_to_hand_slot(self, target_slot: int) -> None:
        """
        Navigates cursor from current hand slot to target slot (0 to 4).
        
        Args:
            target_slot: Zero-based index of the hand card (0..4).
        """
        target_slot = max(0, min(4, target_slot))

        # If hand is not yet focused, focus it first
        if self.current_hand_slot is None:
            self.focus_hand()

        current = self.current_hand_slot if self.current_hand_slot is not None else 0
        delta = target_slot - current

        if delta > 0:
            for _ in range(delta):
                self._press_key("ArrowRight", delay_mult=0.7)
        elif delta < 0:
            for _ in range(abs(delta)):
                self._press_key("ArrowLeft", delay_mult=0.7)

        self.current_hand_slot = target_slot

    def click_hand_card(self, slot_index: int) -> bool:
        """Clicks the hand card directly in DOM to raise/lift it into the fusion queue."""
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
            return bool(self.cdp.eval_js(js))
        except Exception:
            return False

    def lift_card_for_fusion(self) -> None:
        """
        Presses [ArrowUp] to lift the currently focused card into the fusion queue.
        """
        log(f"Lifting card at slot {self.current_hand_slot} for fusion [ArrowUp]...", "FUSION")
        self._press_key("ArrowUp", delay_mult=0.9)

    def trigger_fusion(self) -> None:
        """
        Confirms the fusion after lifting cards.
        Clicks the green checkmark [✔] confirmation button or presses [Enter].
        """
        log("Triggering fusion: clicking [✔] and pressing [Enter]...", "FUSION")
        js_confirm = """
        (() => {
            const btn = Array.from(document.querySelectorAll('button')).find(b => {
                const text = b.innerText.trim();
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                return text === '✔' || text.includes('✔') || aria.includes('confirm') || aria.includes('fuse');
            });
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        })()
        """
        try:
            self.cdp.eval_js(js_confirm)
        except Exception:
            pass

        self._press_key("Enter", delay_mult=1.5)

    def execute_fusion_sequence(self, sequence: List[int]) -> bool:
        """
        High-level orchestrator: Lifts cards in the exact order specified by sequence,
        then starts the fusion.
        
        Args:
            sequence: List of hand card indices in the order they must fuse (e.g. [0, 1]).
        """
        if not sequence:
            log("Empty sequence provided, skipping fusion.", "WARN")
            return False

        log(f"Executing fusion sequence: {[idx + 1 for idx in sequence]}", "FUSION")
        
        # 1. Bring initial focus to hand
        self.focus_hand()

        # 2. Lift each card in sequence using both DOM click and keyboard lift
        for card_idx in sequence:
            self.click_hand_card(card_idx)
            self.navigate_to_hand_slot(card_idx)
            self.lift_card_for_fusion()

        if self.key_delay > 0:
            time.sleep(self.key_delay * 0.8)

        # 3. Trigger the fusion
        self.trigger_fusion()
        return True

    # =========================================================================
    # 2. Field Placement & Monster Summoning
    # =========================================================================

    def place_monster_on_field(self, target_zone: int = 2) -> None:
        """
        Navigates across monster field zones and places the summoned monster.
        Clicks the zone marker circle in DOM (as seen in video) with keyboard fallback.
        
        Args:
            target_zone: Target player field zone (0..4, default 2: middle zone).
        """
        target_zone = max(0, min(4, target_zone))
        log(f"Selecting field zone {target_zone} for monster placement...", "DUEL")

        js_zone = f"""
        (() => {{
            const zones = Array.from(document.querySelectorAll('.zone-marker-btn, [aria-label*="Select zone"]'));
            if (zones.length > 0) {{
                const target = zones[{target_zone}] || zones[0];
                target.click();
                return true;
            }}
            return false;
        }})()
        """
        try:
            self.cdp.eval_js(js_zone)
        except Exception:
            pass

        # Field navigation delta from initial placement cursor (defaults to middle zone 2)
        initial_cursor = 2
        delta = target_zone - initial_cursor

        if delta > 0:
            for _ in range(delta):
                self._press_key("ArrowRight", delay_mult=0.7)
        elif delta < 0:
            for _ in range(abs(delta)):
                self._press_key("ArrowLeft", delay_mult=0.7)

        # Confirm placement
        self._press_key("Enter", delay_mult=1.2)
        self.current_field_zone = target_zone
        log(f"Confirmed placement on zone {target_zone} [Enter].", "SUCCESS")

    # =========================================================================
    # 3. Guardian Star Selection
    # =========================================================================

    def choose_guardian_star(self, choice: Union[int, str] = 1) -> None:
        """
        Selects Guardian Star in modal prompt using DOM click or keys '1' or '2'.
        In the video, Meteor Black Dragon selects 'Sun' (Option 2), and THTD selects 'Pluto' (Option 1).
        
        Args:
            choice: 1, 2, or name string ('Sun', 'Mars', 'Pluto', 'Mercury').
        """
        star_str = str(choice).lower().strip()
        js_click_star = f"""
        (() => {{
            const buttons = Array.from(document.querySelectorAll('button'));
            const target = buttons.find(b => {{
                const txt = (b.innerText || '').toLowerCase();
                const aria = (b.getAttribute('aria-label') || '').toLowerCase();
                return txt.includes('{star_str}') || aria.includes('{star_str}');
            }});
            if (target) {{
                target.click();
                return true;
            }}
            return false;
        }})()
        """
        try:
            if self.cdp.eval_js(js_click_star):
                log(f"Selected Guardian Star '{choice}' via DOM click.", "SUCCESS")
                return
        except Exception:
            pass

        # Normalize choice to key '1' or '2'
        if star_str in ("2", "second", "sun", "mercury", "right", "moon", "neptune"):
            key = "2"
        else:
            key = "1"

        log(f"Selecting Guardian Star option '{key}' via keyboard...", "INFO")
        self._press_key(key, delay_mult=1.0)

    # =========================================================================
    # 4. Combat & Attacking
    # =========================================================================

    def execute_attack(self, player_zone: int = 2, opponent_zone: int = 2) -> None:
        """
        Initiates attack sequence with monster on field:
        1. Navigates to the player's monster on field.
        2. Presses [Enter] to open interaction menu.
        3. Presses [Enter] to select "Attack".
        4. Navigates to opponent's field card / LP direct zone.
        5. Presses [Enter] to execute combat!
        
        Args:
            player_zone: Index of the player monster attacking (0..4).
            opponent_zone: Index of the opponent card to target (0..4).
        """
        log(f"Initiating attack from zone {player_zone} to opponent zone {opponent_zone}...", "COMBAT")

        # 1. Focus player monster zone
        self._press_key("Enter", delay_mult=0.8)

        # 2. Select "Attack" from menu
        self._press_key("Enter", delay_mult=1.0)

        # 3. Navigate to target on opponent's field if needed
        # Default target cursor usually centers on opponent zone 2
        initial_opp_cursor = 2
        delta = opponent_zone - initial_opp_cursor
        if delta > 0:
            for _ in range(delta):
                self._press_key("ArrowRight", delay_mult=0.7)
        elif delta < 0:
            for _ in range(abs(delta)):
                self._press_key("ArrowLeft", delay_mult=0.7)

        # 4. Confirm attack
        self._press_key("Enter", delay_mult=1.2)
        log("Attack executed [Enter].", "SUCCESS")

    # =========================================================================
    # 5. Turn Management
    # =========================================================================

    def end_turn(self) -> None:
        """
        Ends player turn by clicking the 'End turn' button or pressing ['e'].
        Resets cursor tracking for next turn.
        """
        log("Ending turn: clicking 'End turn' / pressing ['e']...", "DUEL")
        js = """
        (() => {
            const btn = document.querySelector('.end-turn') || Array.from(document.querySelectorAll('button')).find(b => b.innerText.toLowerCase().includes('end turn'));
            if (btn) {
                btn.click();
                return true;
            }
            return false;
        })()
        """
        try:
            self.cdp.eval_js(js)
        except Exception:
            pass

        self._press_key("e", delay_mult=1.2)
        self.current_hand_slot = None
