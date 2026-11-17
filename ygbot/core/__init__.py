"""
Core package for YGBot.
Provides low-level browser CDP communication, visual template recognition,
middleware execution pipeline, configuration, and logging utilities.
"""

from .cdp import (
    CDPClient,
    BrowserDriver,
    WebSocketTransport,
    SimpleWebSocket,
    CDPSession,
    CDPDOM,
    CDPInput,
)
from .vision_fallback import ScreenClicker
from .middleware import (
    ActionContext,
    Middleware,
    LoggingMiddleware,
    TimingAndDelayMiddleware,
    VisionFallbackMiddleware,
    ErrorCaptureMiddleware,
    MiddlewarePipeline,
    create_default_pipeline,
)
from .config import Config
from .utils import log, print_banner, format_duration, Colors, format_cards_table, print_cards_table

__all__ = [
    "CDPClient",
    "BrowserDriver",
    "WebSocketTransport",
    "SimpleWebSocket",
    "CDPSession",
    "CDPDOM",
    "CDPInput",
    "ScreenClicker",
    "ActionContext",
    "Middleware",
    "LoggingMiddleware",
    "TimingAndDelayMiddleware",
    "VisionFallbackMiddleware",
    "ErrorCaptureMiddleware",
    "MiddlewarePipeline",
    "create_default_pipeline",
    "Config",
    "log",
    "print_banner",
    "format_duration",
    "format_cards_table",
    "print_cards_table",
    "Colors",
]
