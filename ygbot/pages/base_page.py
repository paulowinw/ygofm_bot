"""
Base Page Object for Adapted Page Object Model (POM).

Encapsulates CDP browser communication wrapped inside the middleware execution pipeline.
All low-level clicks, key inputs, and JS evaluations flow through the pipeline:
Log Action -> Apply Delay -> Execute CDP Action -> (If fail) -> Vision Fallback -> Error Capture.
"""

import time
from typing import Optional, Any, Tuple, Callable
from ..core.cdp_client import CDPClient
from ..core.middleware import MiddlewarePipeline, create_default_pipeline
from ..core.vision_fallback import ScreenClicker
from ..core.config import Config


class BasePage:
    """
    Abstract Page Object providing unified, middleware-wrapped browser interactions.
    """

    def __init__(
        self,
        cdp: CDPClient,
        config: Optional[Config] = None,
        pipeline: Optional[MiddlewarePipeline] = None,
        vision: Optional[ScreenClicker] = None,
    ):
        self.cdp = cdp
        self.cfg = config or Config.load()
        self.vision = vision or ScreenClicker(self.cfg)
        self.pipeline = pipeline or create_default_pipeline(
            cdp_client=self.cdp,
            vision_clicker=self.vision,
            action_delay=getattr(self.cfg, "action_delay", 0.35),
        )

    def click(
        self,
        x: Optional[float] = None,
        y: Optional[float] = None,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        fallback_coords: Optional[Tuple[float, float]] = None,
        description: Optional[str] = None,
        turn_number: int = 1,
        delay: Optional[float] = None,
    ) -> bool:
        """
        Executes a click through the middleware pipeline.
        Supports normalized coordinate clicking, DOM selector matching, or visible text matching.
        """
        desc = description or f"Click({text or selector or (x, y)})"

        def _do_click() -> bool:
            if text:
                return self.cdp.click_element_by_text(text)
            if selector:
                # Query element coordinates and click via CDP
                js = f"""
                (() => {{
                    const el = document.querySelector({repr(selector)});
                    if (!el) return null;
                    el.scrollIntoView({{block: 'center', inline: 'center'}});
                    const rect = el.getBoundingClientRect();
                    el.click();
                    return {{x: rect.x + rect.width / 2, y: rect.y + rect.height / 2}};
                }})()
                """
                res = self.cdp.eval_js(js)
                if res and isinstance(res, dict) and "x" in res:
                    self.cdp.click_at(int(res["x"]), int(res["y"]))
                    return True
                return bool(res)
            if x is not None and y is not None:
                screen_x = int(x * self.cdp.viewport_width)
                screen_y = int(y * self.cdp.viewport_height)
                self.cdp.click_at(screen_x, screen_y)
                return True
            return False

        fb = fallback_coords or ((x, y) if (x is not None and y is not None) else None)
        return self.pipeline.run(
            action_name="Click",
            action_type="CLICK",
            handler=_do_click,
            turn_number=turn_number,
            fallback_coords=fb,
            description=desc,
            delay=delay,
        )

    def send_key(
        self,
        key_name: str,
        delay_mult: float = 1.0,
        description: Optional[str] = None,
        turn_number: int = 1,
    ):
        """Dispatches keyboard input through the middleware pipeline."""
        desc = description or f"Key [{key_name}]"
        delay = getattr(self.cfg, "action_delay", 0.35) * delay_mult

        def _do_key():
            self.cdp.send_key(key_name, delay=0.04 if delay > 0 else 0.0)
            return True

        return self.pipeline.run(
            action_name="SendKey",
            action_type="KEY",
            handler=_do_key,
            turn_number=turn_number,
            description=desc,
            delay=delay,
        )

    def eval_js(
        self,
        script: str,
        description: Optional[str] = None,
        turn_number: int = 1,
    ) -> Any:
        """Evaluates JavaScript expression through the middleware pipeline."""
        desc = description or "Evaluate JavaScript"
        return self.pipeline.run(
            action_name="EvalJS",
            action_type="EVAL",
            handler=lambda: self.cdp.eval_js(script),
            turn_number=turn_number,
            description=desc,
            delay=0.0,
        )

    def wait_for(
        self,
        condition_fn: Callable[[], bool],
        timeout: float = 5.0,
        poll_interval: float = 0.2,
    ) -> bool:
        """Polls until condition_fn returns True or timeout expires."""
        deadline = time.time() + timeout
        while time.time() < deadline:
            try:
                if condition_fn():
                    return True
            except Exception:
                pass
            time.sleep(poll_interval)
        return False
