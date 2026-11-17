"""
Core package for YGBot.
Provides low-level browser CDP communication, visual template recognition,
middleware execution pipeline, configuration, and logging utilities.
"""

from .cdp_client import CDPClient, SimpleWebSocket
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
from .utils import log, print_banner, format_duration, Colors

__all__ = [
    "CDPClient",
    "SimpleWebSocket",
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
    "Colors",
]
