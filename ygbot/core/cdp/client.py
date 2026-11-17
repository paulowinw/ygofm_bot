"""
CDPClient Facade.

Design Pattern: Facade Pattern (GoF)
Exposes a unified, clean interface for Google Chrome browser automation
while delegating low-level operations to specialized subsystems:
- transport: Raw socket connections & RFC 6455 framing
- session: Tab querying, target management, & JSON-RPC correlation
- dom: Viewport sizing, JS evaluation, & DOM element bounding box queries
- input: Mouse clicking, coordinate scaling, & physical/synthetic keyboard dispatching
"""

from typing import Optional, Dict, Any, List, Tuple
from .session import CDPSession
from .dom import CDPDOM
from .input import CDPInput
from .transport import WebSocketTransport, SimpleWebSocket


class CDPClient:
    """
    Facade for automating Google Chrome via Chrome DevTools Protocol.
    
    Hides the complexity of raw WebSocket framing, JSON-RPC correlation,
    DOM queries, and keyboard/mouse dispatching behind a clean, cohesive API.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9222):
        self.host = host
        self.port = port

        # Subsystems
        self.session = CDPSession(host=host, port=port)
        self.dom = CDPDOM(self.session)
        self.input = CDPInput(self.session, self.dom)

    # --- Properties ---

    @property
    def viewport_width(self) -> int:
        """Current viewport width in pixels."""
        return self.dom.viewport_width

    @viewport_width.setter
    def viewport_width(self, value: int):
        self.dom.viewport_width = value

    @property
    def viewport_height(self) -> int:
        """Current viewport height in pixels."""
        return self.dom.viewport_height

    @viewport_height.setter
    def viewport_height(self, value: int):
        self.dom.viewport_height = value

    @property
    def target_tab(self) -> Optional[Dict[str, Any]]:
        """Active target tab metadata dictionary."""
        return self.session.target_tab

    @property
    def ws(self) -> Optional[WebSocketTransport]:
        """Underlying active WebSocket transport."""
        return self.session.transport

    @property
    def is_connected(self) -> bool:
        """True if session transport is active."""
        return self.session.is_connected

    # --- Tab Discovery & Connection ---

    def is_chrome_running(self) -> bool:
        """Checks if Chrome is listening on the remote debugging port."""
        return self.session.is_chrome_running()

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Fetches list of all open page tabs."""
        return self.session.get_tabs()

    def find_game_tab(self, patterns: List[str]) -> Optional[Dict[str, Any]]:
        """Finds browser tab matching game keywords."""
        return self.session.find_tab(patterns)

    def connect(self, tab: Optional[Dict[str, Any]] = None):
        """Connects to target tab via WebSocket and queries initial viewport metrics."""
        self.session.connect(tab)
        self.dom.update_viewport_size()

    # --- Protocol & DOM Primitives ---

    def send_cmd(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Sends a CDP JSON-RPC command and returns the result."""
        return self.session.send_cmd(method, params, timeout=timeout)

    def eval_js(self, expr: str) -> Any:
        """Evaluates a JavaScript expression in the tab context."""
        return self.dom.eval_js(expr)

    def update_viewport_size(self) -> Tuple[int, int]:
        """Refreshes layout viewport dimensions."""
        return self.dom.update_viewport_size()

    # --- Mouse & Keyboard Inputs ---

    def click_at(self, x: float, y: float, delay: float = 0.05):
        """Simulates physical mouse click at pixel coordinates (x, y)."""
        self.input.click_at(x, y, delay=delay)

    def click_percent(self, x_pct: float, y_pct: float, delay: float = 0.05):
        """Simulates physical mouse click at relative percentage coordinates (0.0 to 1.0)."""
        self.input.click_percent(x_pct, y_pct, delay=delay)

    def click_element_by_text(self, text: str, tag: str = "*") -> bool:
        """Locates a DOM element by text content and clicks it."""
        return self.input.click_element_by_text(text, tag=tag)

    def send_key(self, key_name: str, delay: float = 0.05):
        """Dispatches a physical keyboard key press and DOM fallback via CDP."""
        self.input.send_key(key_name, delay=delay)

    def close(self):
        """Closes active WebSocket connection."""
        self.session.close()


# Architectural alias
BrowserDriver = CDPClient
