"""
CDP Session & Lifecycle Manager.

Manages Chrome discovery endpoints (/json/list, /json/version),
WebSocket lifecycle for browser tabs, and JSON-RPC command correlation.
"""

import json
import time
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List
from .transport import WebSocketTransport


class CDPSession:
    """
    Manages browser tab discovery, active WebSocket session lifecycle,
    and synchronous JSON-RPC request-response dispatching.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9222):
        self.host = host
        self.port = port
        self.transport: Optional[WebSocketTransport] = None
        self.target_tab: Optional[Dict[str, Any]] = None
        self.msg_id = 1

    @property
    def is_connected(self) -> bool:
        """Indicates if an active WebSocket session is open."""
        return self.transport is not None and self.transport.is_connected

    def is_chrome_running(self) -> bool:
        """Checks if Chrome is listening on the remote debugging port."""
        try:
            url = f"http://{self.host}:{self.port}/json/version"
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_tabs(self) -> List[Dict[str, Any]]:
        """Fetches list of all open page tabs from the Chrome HTTP endpoint."""
        url = f"http://{self.host}:{self.port}/json/list"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [t for t in data if t.get("type") == "page"]

    def find_tab(self, patterns: List[str]) -> Optional[Dict[str, Any]]:
        """Finds a browser tab matching URL or title keywords."""
        tabs = self.get_tabs()
        for tab in tabs:
            tab_url = tab.get("url", "").lower()
            tab_title = tab.get("title", "").lower()
            for pat in patterns:
                pat_lower = pat.lower()
                if pat_lower in tab_url or pat_lower in tab_title:
                    return tab

        # Generic duel/game tab fallback
        for tab in tabs:
            tab_title = tab.get("title", "").lower()
            if any(k in tab_title for k in ["forbidden", "memories", "duel", "yugioh"]):
                return tab

        # Single tab fallback
        if len(tabs) == 1:
            return tabs[0]

        return None

    def connect(self, tab: Optional[Dict[str, Any]] = None) -> WebSocketTransport:
        """Connects to a target tab via WebSocket."""
        if not tab:
            tabs = self.get_tabs()
            if not tabs:
                raise RuntimeError("No open tabs found in Chrome.")
            tab = tabs[0]

        self.target_tab = tab
        ws_url = tab.get("webSocketDebuggerUrl")
        if not ws_url:
            raise RuntimeError(f"Tab does not have a webSocketDebuggerUrl: {tab}")

        # Parse ws://host:port/path
        without_scheme = ws_url.replace("ws://", "")
        host_port, path = without_scheme.split("/", 1)
        path = "/" + path
        if ":" in host_port:
            h, p = host_port.split(":")
            p = int(p)
        else:
            h, p = host_port, 80

        self.transport = WebSocketTransport(h, p, path)
        self.transport.connect()
        return self.transport

    def send_cmd(self, method: str, params: Optional[Dict[str, Any]] = None, timeout: float = 10.0) -> Dict[str, Any]:
        """Sends a CDP JSON-RPC command and waits for the matching response."""
        if not self.transport or not self.transport.is_connected:
            raise ConnectionError("CDP WebSocket not connected")

        current_id = self.msg_id
        self.msg_id += 1

        msg = {"id": current_id, "method": method}
        if params is not None:
            msg["params"] = params

        self.transport.send_text(json.dumps(msg))

        # Read responses until we find the one with matching id
        deadline = time.time() + timeout
        while time.time() < deadline:
            raw = self.transport.recv_text()
            try:
                resp = json.loads(raw)
            except Exception:
                continue

            if resp.get("id") == current_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP command {method} failed: {resp['error']}")
                return resp.get("result", {})

        raise TimeoutError(f"Timed out waiting for CDP response for {method} (id={current_id})")

    def close(self):
        """Closes active WebSocket connection."""
        if self.transport:
            self.transport.close()
            self.transport = None
        self.target_tab = None
