"""
Middleware execution pipeline for browser and vision actions.

Design Pattern: Chain of Responsibility / Pipeline Pattern
Flow:
    Request -> [LoggingMiddleware] -> [DelayMiddleware] -> [Execute Action]
            -> (On failure) -> [VisionFallbackMiddleware] -> [ErrorCaptureMiddleware]
"""

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional
from .utils import log, Colors


@dataclass
class ActionContext:
    """Encapsulates context, parameters, and results of an action in the bot pipeline."""
    action_name: str
    action_type: str = "CLICK"  # CLICK, KEY, EVAL, VISION, FUSION, STATE
    params: Dict[str, Any] = field(default_factory=dict)
    result: Any = None
    success: bool = True
    error: Optional[Exception] = None
    turn_number: int = 1
    start_time: float = field(default_factory=time.time)
    duration: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)


class Middleware(ABC):
    """Abstract base middleware in the execution chain."""

    @abstractmethod
    def execute(self, context: ActionContext, next_handler: Callable[[ActionContext], Any]) -> Any:
        """Processes the action context and delegates to the next handler in the pipeline."""
        pass


class LoggingMiddleware(Middleware):
    """Logs action initiation and result to console."""

    def execute(self, context: ActionContext, next_handler: Callable[[ActionContext], Any]) -> Any:
        desc = context.params.get("description", context.action_name)
        log(f"[Turn {context.turn_number}] Executing: {desc}...", "DUEL")
        
        start = time.time()
        try:
            result = next_handler(context)
            context.duration = time.time() - start
            context.result = result
            context.success = True if result is not False else False
            
            status_text = "Success" if context.success else "Action returned False"
            log(f"[Turn {context.turn_number}] {desc} -> {status_text} ({context.duration:.2f}s)", "SUCCESS" if context.success else "WARN")
            return result
        except Exception as e:
            context.duration = time.time() - start
            context.success = False
            context.error = e
            log(f"[Turn {context.turn_number}] {desc} -> Failed: {e}", "ERROR")
            raise


class TimingAndDelayMiddleware(Middleware):
    """Applies configured pre/post action delay."""

    def __init__(self, action_delay: float = 0.35):
        self.action_delay = action_delay

    def execute(self, context: ActionContext, next_handler: Callable[[ActionContext], Any]) -> Any:
        delay = context.params.get("delay")
        if delay is None:
            delay = self.action_delay
        result = next_handler(context)
        if delay and delay > 0:
            time.sleep(delay)
        return result


class VisionFallbackMiddleware(Middleware):
    """
    Fallback handler: If CDP click fails or element is not found in DOM,
    triggers visual coordinate / ScreenClicker fallback.
    """

    def __init__(self, vision_clicker: Optional[Any] = None):
        self.vision = vision_clicker

    def execute(self, context: ActionContext, next_handler: Callable[[ActionContext], Any]) -> Any:
        try:
            result = next_handler(context)
            if result is not False and result is not None:
                return result
        except Exception as e:
            context.error = e

        # If primary DOM/CDP action returned False or threw, check for coordinate/vision fallback
        fallback_coords = context.params.get("fallback_coords")
        if fallback_coords and self.vision:
            log(f"DOM action failed, triggering Vision/Coordinate fallback at {fallback_coords}...", "WARN")
            try:
                self.vision.click_percent(fallback_coords[0], fallback_coords[1])
                context.success = True
                context.metadata["fallback_used"] = True
                return True
            except Exception as fe:
                log(f"Vision fallback failed: {fe}", "ERROR")
                context.error = fe
                return False

        if context.error:
            raise context.error
        return context.result


class ErrorCaptureMiddleware(Middleware):
    """Captures error state and diagnostic screenshots on critical failures."""

    def __init__(self, cdp_client: Optional[Any] = None):
        self.cdp = cdp_client

    def execute(self, context: ActionContext, next_handler: Callable[[ActionContext], Any]) -> Any:
        try:
            return next_handler(context)
        except Exception as e:
            context.success = False
            context.error = e
            log(f"Error captured in action '{context.action_name}': {e}", "ERROR")
            if self.cdp:
                try:
                    # Attempt diagnostic screenshot if client supports it
                    if hasattr(self.cdp, "capture_screenshot"):
                        shot_path = f"/tmp/ygbot_error_{int(time.time())}.png"
                        self.cdp.capture_screenshot(shot_path)
                        log(f"Diagnostic screenshot saved to {shot_path}", "WARN")
                except Exception:
                    pass
            raise


class MiddlewarePipeline:
    """Manages ordered execution of middlewares around arbitrary target actions."""

    def __init__(self, middlewares: Optional[List[Middleware]] = None):
        self.middlewares: List[Middleware] = middlewares or []

    def add(self, middleware: Middleware) -> "MiddlewarePipeline":
        self.middlewares.append(middleware)
        return self

    def run(self, action_name: str, action_type: str, handler: Callable[[], Any], turn_number: int = 1, **params) -> Any:
        """Runs the given target callable wrapped inside the middleware pipeline."""
        context = ActionContext(
            action_name=action_name,
            action_type=action_type,
            params=params,
            turn_number=turn_number,
        )

        def create_chain(idx: int) -> Callable[[ActionContext], Any]:
            if idx >= len(self.middlewares):
                return lambda ctx: handler()
            mw = self.middlewares[idx]
            next_fn = create_chain(idx + 1)
            return lambda ctx: mw.execute(ctx, next_fn)

        chain = create_chain(0)
        return chain(context)


def create_default_pipeline(
    cdp_client: Optional[Any] = None,
    vision_clicker: Optional[Any] = None,
    action_delay: float = 0.35,
) -> MiddlewarePipeline:
    """
    Factory that constructs the canonical execution pipeline:
    Log Action -> Apply Delay -> Execute CDP Click -> (If fail) -> Trigger Vision Fallback -> Capture Error Screen.
    """
    return MiddlewarePipeline([
        LoggingMiddleware(),
        ErrorCaptureMiddleware(cdp_client=cdp_client),
        TimingAndDelayMiddleware(action_delay=action_delay),
        VisionFallbackMiddleware(vision_clicker=vision_clicker),
    ])

