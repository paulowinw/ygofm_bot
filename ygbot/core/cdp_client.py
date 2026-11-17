"""
Chrome DevTools Protocol (CDP) Client.

Backward-compatibility facade module.
The decoupled CDP architecture is implemented under `ygbot.core.cdp`:
- `ygbot.core.cdp.transport` (WebSocket transport & framing)
- `ygbot.core.cdp.session` (Discovery, lifecycle & JSON-RPC)
- `ygbot.core.cdp.dom` (Viewport & JS evaluation)
- `ygbot.core.cdp.input` (Mouse & keyboard dispatching)
- `ygbot.core.cdp.client` (The Facade)
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

__all__ = [
    "CDPClient",
    "BrowserDriver",
    "WebSocketTransport",
    "SimpleWebSocket",
    "CDPSession",
    "CDPDOM",
    "CDPInput",
]
