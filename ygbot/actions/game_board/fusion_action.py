"""
Fusion Action for GameBoardPage.

Responsibilities:
- Main fusion logic coordinating strategy evaluation and board execution.
- Evaluates hand cards against ordered FusionStrategy implementations (Meteor Black Dragon, THTD, Highest ATK, etc.).
- Executes the sequence of clicks for fusions on the game board.
- Triggers the fusion calculation on the canvas/emulator.
- Logs the resulting card's name, ATK, and DEF to the console.
"""

from typing import List, Dict, Optional, Tuple, Union, Any
from ..base_action import BaseAction
from ...pages.game_board_page import GameBoardPage
from ...features.cards.models import Card
from ...features.cards.registry import CardRegistry
from ...features.cards.known_cards import KNOWN_CARDS
from ...features.fusion.result import FusionResult
from ...features.fusion.strategy import (
    FusionStrategy,
    MeteorBlackDragonStrategy,
    THTDFusionStrategy,
    DiscardAndCycleStrategy,
    EquipBuffStrategy,
    ElementalFusionStrategy,
    HighestAtkStrategy,
)
from ...core.utils import log, Colors


class FusionAction(BaseAction):
    """
    Action that encapsulates the main fusion logic:
    - Builds and coordinates fusion strategies.
    - Solves a hand of cards to produce a FusionResult.
    - Executes the fusion sequence on the game board.
    - Logs the fusion result name, ATK, and DEF to the console.
    """

    def __init__(
        self,
        page: Optional[GameBoardPage] = None,
        strategy: str = "THTD",
        registry: Optional[CardRegistry] = None,
    ):
        super().__init__(page)
        self.strategy_name = strategy
        self.registry = registry or CardRegistry.get_instance()
        self.strategies: List[FusionStrategy] = self._build_strategies(strategy)

    @property
    def name(self) -> str:
        return "Fusion"

    def _build_strategies(self, strategy_name: str) -> List[FusionStrategy]:
        """Builds the ordered evaluation chain of strategies."""
        name_clean = strategy_name.strip().lower() if strategy_name else "thtd"

        if name_clean == "highest_atk":
            return [
                HighestAtkStrategy(),
                MeteorBlackDragonStrategy(),
                THTDFusionStrategy(),
                DiscardAndCycleStrategy(),
                EquipBuffStrategy(),
                ElementalFusionStrategy(),
            ]

        return [
            MeteorBlackDragonStrategy(),
            THTDFusionStrategy(),
            DiscardAndCycleStrategy(),
            EquipBuffStrategy(),
            ElementalFusionStrategy(),
            HighestAtkStrategy(),
        ]

    def register_strategy(self, strategy: FusionStrategy, prepend: bool = False):
        """Registers a custom strategy at runtime (Open/Closed Principle)."""
        if prepend:
            self.strategies.insert(0, strategy)
        else:
            self.strategies.append(strategy)

    def solve_hand(self, hand: List[Union[str, Dict[str, Any], Card]]) -> FusionResult:
        """
        Given a hand of cards, normalizes them into Card domain models
        and evaluates strategies in priority order.
        """
        if not hand:
            return FusionResult(sequence=[], play_name="Empty Hand", estimated_atk=0)

        card_models: List[Card] = [
            self.registry.from_any(item, index=i)
            for i, item in enumerate(hand)
        ]

        for strategy in self.strategies:
            result = strategy.evaluate(card_models)
            if result is not None:
                return result

        first_card = card_models[0]
        return FusionResult(
            sequence=[0],
            play_name=first_card.name,
            estimated_atk=getattr(first_card, "atk", 1000),
        )

    def execute(
        self,
        target: Union[FusionResult, List[Union[str, Dict[str, Any], Card]]],
        turn_number: int = 1,
        board_page: Optional[Any] = None,
    ) -> bool:
        """
        Executes sequence of card clicks on the board and confirms fusion,
        then prints the resulting card name, ATK, and DEF to the console.
        
        target can be either a FusionResult or a list of hand cards (which will be solved first).
        """
        if isinstance(target, list):
            result = self.solve_hand(target)
        else:
            result = target

        if not result or not result.sequence:
            log(f"[Turn {turn_number}] No valid fusion sequence to execute.", "WARN")
            return False

        page = board_page or self.page
        if not page:
            log(f"[Turn {turn_number}] No GameBoardPage attached to execute fusion.", "ERROR")
            return False

        seq_display = [i + 1 for i in result.sequence]
        log(f"[Turn {turn_number}] Executing fusion sequence: {seq_display} -> {result.play_name}", "FUSION")

        # 1. Request specific card interactions on the Page Object
        for slot in result.sequence:
            page.click_card_at_slot(slot, turn_number=turn_number)

        # 2. Trigger fusion confirmation
        success = page.trigger_fusion(turn_number=turn_number)

        # 3. Resolve resulting card ATK and DEF
        fusion_name = result.play_name
        atk, def_ = self._resolve_card_stats(fusion_name, result.estimated_atk)

        # 4. Log the result to the console: name, ATK, and DEF
        log(
            f"[Turn {turn_number}] Fusion performed: {Colors.BOLD}{fusion_name}{Colors.END} -> "
            f"ATK: {Colors.GREEN}{atk}{Colors.END} | DEF: {Colors.CYAN}{def_}{Colors.END}",
            "SUCCESS",
        )

        return success

    def execute_fusion(self, result: FusionResult, board_page: Optional[Any] = None, turn_number: int = 1) -> bool:
        """
        Backward-compatible execution method matching legacy FusionEngine signature.
        """
        return self.execute(target=result, turn_number=turn_number, board_page=board_page)

    def _resolve_card_stats(self, play_name: str, estimated_atk: int = 0) -> Tuple[int, int]:
        """Looks up or estimates attack and defense points for the resulting fusion monster."""
        # 1. Exact catalog match
        if play_name in KNOWN_CARDS:
            entry = KNOWN_CARDS[play_name]
            atk = entry.get("atk", estimated_atk)
            def_ = entry.get("def", 1000)
            return atk, def_

        # 2. Canonical fusion recipes
        lower = play_name.lower()
        if "twin-headed" in lower or "thtd" in lower:
            return max(estimated_atk, 2800), 2100
        if "meteor black" in lower:
            return max(estimated_atk, 3500), 2000
        if "black forest" in lower:
            return max(estimated_atk, 2100), 1800
        if "flame cerebrus" in lower:
            return max(estimated_atk, 2100), 1800
        if "mystical sand" in lower:
            return max(estimated_atk, 2100), 1700
        if "equipped" in lower or "buffed" in lower:
            return estimated_atk, 1500

        return estimated_atk, 1500


# Backward compatibility alias
FusionEngine = FusionAction
