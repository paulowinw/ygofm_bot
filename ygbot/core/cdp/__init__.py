"""
Chrome DevTools Protocol (CDP) Subsystem Architecture.

Deconstructs monolithic CDP client into specialized, decoupled components:
- transport: Raw socket connections & RFC 6455 WebSocket framing
- session: Tab querying, WebSocket lifecycle, & JSON-RPC dispatching
- dom: Viewport sizing, JS evaluation, & DOM element bounding box queries
- input: Mouse clicks, coordinate scaling, & physical/synthetic keyboard dispatching
- client: The Facade (CDPClient / BrowserDriver) exposing unified API
"""

from .transport import WebSocketTransport, SimpleWebSocket
from .session import CDPSession
from .dom import CDPDOM
from .input import CDPInput
from .client import CDPClient, BrowserDriver

__all__ = [
    "CDPClient",
    "BrowserDriver",
    "WebSocketTransport",
    "SimpleWebSocket",
    "CDPSession",
    "CDPDOM",
    "CDPInput",
]
