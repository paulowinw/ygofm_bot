"""
Chrome DevTools Protocol (CDP) Client for YGBot.
Connects directly to Google Chrome via remote debugging port without requiring Selenium/WebDriver.
Pure Python standard library implementation (RFC 6455 WebSocket).
"""

import os
import sys
import json
import time
import socket
import struct
import base64
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List, Tuple
from .utils import log

class SimpleWebSocket:
    """A lightweight, zero-dependency RFC 6455 WebSocket client."""

    def __init__(self, host: str, port: int, path: str, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.path = path
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._connected = False

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

        # RFC 6455 Handshake
        key = base64.b64encode(os.urandom(16)).decode('ascii')
        handshake_req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake_req.encode("utf-8"))

        # Read response
        header_data = b""
        while b"\r\n\r\n" not in header_data:
            chunk = self.sock.recv(4096)
            if not chunk:
                raise ConnectionError("WebSocket connection closed during handshake")
            header_data += chunk

        lines = header_data.split(b"\r\n")
        status_line = lines[0].decode("latin-1")
        if "101" not in status_line:
            raise ConnectionError(f"WebSocket handshake failed: {status_line}")

        self._connected = True

    def send_text(self, payload: str):
        if not self._connected or not self.sock:
            raise ConnectionError("WebSocket not connected")
        payload_bytes = payload.encode("utf-8")
        length = len(payload_bytes)

        # Masking is required for client-to-server frames
        mask_key = os.urandom(4)
        b1 = 0x81  # FIN=1, opcode=1 (text)
        
        if length <= 125:
            header = struct.pack("!BB", b1, 0x80 | length)
        elif length <= 65535:
            header = struct.pack("!BBH", b1, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", b1, 0x80 | 127, length)

        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload_bytes))
        self.sock.sendall(header + mask_key + masked)

    def recv_text(self) -> str:
        if not self._connected or not self.sock:
            raise ConnectionError("WebSocket not connected")

        # Read 2-byte header
        header = self._recv_exact(2)
        b1, b2 = struct.unpack("!BB", header)
        opcode = b1 & 0x0F
        is_masked = (b2 & 0x80) != 0
        length = b2 & 0x7F

        if length == 126:
            ext_len = self._recv_exact(2)
            length, = struct.unpack("!H", ext_len)
        elif length == 127:
            ext_len = self._recv_exact(8)
            length, = struct.unpack("!Q", ext_len)

        if is_masked:
            mask = self._recv_exact(4)
            data = self._recv_exact(length)
            payload = bytes(b ^ mask[i % 4] for i, b in enumerate(data))
        else:
            payload = self._recv_exact(length)

        if opcode == 0x8:  # Close frame
            self.close()
            raise ConnectionResetError("WebSocket received close frame")
        elif opcode == 0x9:  # Ping frame
            # Respond with pong (opcode 0xA)
            self._send_pong(payload)
            return self.recv_text()

        return payload.decode("utf-8", errors="replace")

    def _recv_exact(self, num_bytes: int) -> bytes:
        data = bytearray()
        while len(data) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionResetError("Connection lost while reading")
            data.extend(chunk)
        return bytes(data)

    def _send_pong(self, data: bytes):
        mask_key = os.urandom(4)
        length = len(data)
        b1 = 0x8A  # FIN=1, opcode=10 (pong)
        header = struct.pack("!BB", b1, 0x80 | length)
        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))
        self.sock.sendall(header + mask_key + masked)

    def close(self):
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None


class CDPClient:
    """
    Client for automating Google Chrome via Chrome DevTools Protocol.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 9222):
        self.host = host
        self.port = port
        self.ws: Optional[SimpleWebSocket] = None
        self.msg_id = 1
        self.target_tab: Optional[Dict] = None
        self.viewport_width = 1920
        self.viewport_height = 1080

    def is_chrome_running(self) -> bool:
        """Checks if Chrome is listening on the remote debugging port."""
        try:
            url = f"http://{self.host}:{self.port}/json/version"
            with urllib.request.urlopen(url, timeout=2.0) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_tabs(self) -> List[Dict]:
        """Fetches list of all open browser tabs."""
        url = f"http://{self.host}:{self.port}/json/list"
        with urllib.request.urlopen(url, timeout=3.0) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return [t for t in data if t.get("type") == "page"]

    def find_game_tab(self, patterns: List[str]) -> Optional[Dict]:
        """Finds the browser tab matching game keywords."""
        tabs = self.get_tabs()
        for tab in tabs:
            tab_url = tab.get("url", "").lower()
            tab_title = tab.get("title", "").lower()
            for pat in patterns:
                pat_lower = pat.lower()
                if pat_lower in tab_url or pat_lower in tab_title:
                    return tab
        
        # If no specific pattern matched, check for generic duel/game tabs
        for tab in tabs:
            tab_title = tab.get("title", "").lower()
            if any(k in tab_title for k in ["forbidden", "memories", "duel", "yugioh"]):
                return tab

        # Return first available page tab if only one exists
        if len(tabs) == 1:
            return tabs[0]

        return None

    def connect(self, tab: Optional[Dict] = None):
        """Connects to target tab via WebSocket."""
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
        # Format: ws://127.0.0.1:9222/devtools/page/...
        without_scheme = ws_url.replace("ws://", "")
        host_port, path = without_scheme.split("/", 1)
        path = "/" + path
        if ":" in host_port:
            h, p = host_port.split(":")
            p = int(p)
        else:
            h, p = host_port, 80

        self.ws = SimpleWebSocket(h, p, path)
        self.ws.connect()

        # Update viewport metrics
        self.update_viewport_size()

    def send_cmd(self, method: str, params: Optional[Dict] = None) -> Dict:
        """Sends a CDP JSON-RPC command and waits for the matching response."""
        if not self.ws:
            raise ConnectionError("CDP WebSocket not connected")

        current_id = self.msg_id
        self.msg_id += 1

        msg = {"id": current_id, "method": method}
        if params is not None:
            msg["params"] = params

        self.ws.send_text(json.dumps(msg))

        # Read responses until we find the one with matching id
        deadline = time.time() + 10.0
        while time.time() < deadline:
            raw = self.ws.recv_text()
            try:
                resp = json.loads(raw)
            except Exception:
                continue

            if resp.get("id") == current_id:
                if "error" in resp:
                    raise RuntimeError(f"CDP command {method} failed: {resp['error']}")
                return resp.get("result", {})

        raise TimeoutError(f"Timed out waiting for CDP response for {method} (id={current_id})")

    def eval_js(self, expr: str) -> Any:
        """Evaluates JavaScript expression in the tab and returns value."""
        res = self.send_cmd("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": True,
            "awaitPromise": True
        })
        result_obj = res.get("result", {})
        return result_obj.get("value")

    def update_viewport_size(self):
        """Fetches layout viewport size."""
        try:
            metrics = self.send_cmd("Page.getLayoutMetrics")
            viewport = metrics.get("cssLayoutViewport", {})
            self.viewport_width = viewport.get("clientWidth", 1920)
            self.viewport_height = viewport.get("clientHeight", 1080)
        except Exception:
            # Fallback via JavaScript
            dims = self.eval_js("[window.innerWidth, window.innerHeight]")
            if dims and len(dims) == 2:
                self.viewport_width = dims[0]
                self.viewport_height = dims[1]

    def click_at(self, x: float, y: float, delay: float = 0.05):
        """Simulates physical mouse click at pixel coordinates (x, y)."""
        self.send_cmd("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": int(x),
            "y": int(y),
            "button": "left",
            "clickCount": 1
        })
        time.sleep(delay)
        self.send_cmd("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": int(x),
            "y": int(y),
            "button": "left",
            "clickCount": 1
        })

    def click_percent(self, x_pct: float, y_pct: float, delay: float = 0.05):
        """Simulates physical mouse click at relative percentage coordinates (0.0 to 1.0)."""
        x = x_pct * self.viewport_width
        y = y_pct * self.viewport_height
        self.click_at(x, y, delay)

    def send_key(self, key_name: str, delay: float = 0.05):
        """
        Dispatches a physical keyboard key press (keydown + keyup) via Chrome DevTools Protocol.
        Compatible with WebGL Canvas, Emulators, and standard DOM keyboard event listeners.
        """
        key_defs = {
            "ArrowDown": {"key": "ArrowDown", "code": "ArrowDown", "windowsVirtualKeyCode": 40, "nativeVirtualKeyCode": 40},
            "ArrowUp": {"key": "ArrowUp", "code": "ArrowUp", "windowsVirtualKeyCode": 38, "nativeVirtualKeyCode": 38},
            "ArrowLeft": {"key": "ArrowLeft", "code": "ArrowLeft", "windowsVirtualKeyCode": 37, "nativeVirtualKeyCode": 37},
            "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "windowsVirtualKeyCode": 39, "nativeVirtualKeyCode": 39},
            "Enter": {"key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13, "text": "\r"},
            "e": {"key": "e", "code": "KeyE", "windowsVirtualKeyCode": 69, "nativeVirtualKeyCode": 69, "text": "e"},
            "E": {"key": "E", "code": "KeyE", "windowsVirtualKeyCode": 69, "nativeVirtualKeyCode": 69, "text": "E"},
            "1": {"key": "1", "code": "Digit1", "windowsVirtualKeyCode": 49, "nativeVirtualKeyCode": 49, "text": "1"},
            "2": {"key": "2", "code": "Digit2", "windowsVirtualKeyCode": 50, "nativeVirtualKeyCode": 50, "text": "2"},
        }

        key_info = key_defs.get(key_name, {
            "key": key_name,
            "code": key_name,
            "windowsVirtualKeyCode": ord(key_name[0].upper()) if len(key_name) == 1 else 0,
            "nativeVirtualKeyCode": ord(key_name[0].upper()) if len(key_name) == 1 else 0,
            "text": key_name if len(key_name) == 1 else ""
        })

        # 1. Dispatch native CDP key events
        try:
            down_params = {
                "type": "rawKeyDown",
                "key": key_info["key"],
                "code": key_info["code"],
                "windowsVirtualKeyCode": key_info.get("windowsVirtualKeyCode", 0),
                "nativeVirtualKeyCode": key_info.get("nativeVirtualKeyCode", 0),
            }
            if "text" in key_info and key_info["text"]:
                down_params["text"] = key_info["text"]

            self.send_cmd("Input.dispatchKeyEvent", down_params)

            if "text" in key_info and key_info["text"]:
                self.send_cmd("Input.dispatchKeyEvent", {
                    "type": "char",
                    "text": key_info["text"],
                    "key": key_info["key"],
                    "code": key_info["code"],
                })

            time.sleep(delay)

            up_params = {
                "type": "keyUp",
                "key": key_info["key"],
                "code": key_info["code"],
                "windowsVirtualKeyCode": key_info.get("windowsVirtualKeyCode", 0),
                "nativeVirtualKeyCode": key_info.get("nativeVirtualKeyCode", 0),
            }
            self.send_cmd("Input.dispatchKeyEvent", up_params)
        except Exception as e:
            log(f"CDP key dispatch error for '{key_name}': {e}", "WARN")

        # 2. DOM fallback event dispatch (ensures canvas / game window captures event)
        js_dispatch = f"""
        (() => {{
            const key = '{key_info["key"]}';
            const code = '{key_info["code"]}';
            const keyCode = {key_info.get("windowsVirtualKeyCode", 0)};
            const target = document.activeElement || document.querySelector('canvas') || document.body || window;
            const downEvt = new KeyboardEvent('keydown', {{ key: key, code: code, keyCode: keyCode, which: keyCode, bubbles: true, cancelable: true }});
            target.dispatchEvent(downEvt);
            const upEvt = new KeyboardEvent('keyup', {{ key: key, code: code, keyCode: keyCode, which: keyCode, bubbles: true, cancelable: true }});
            target.dispatchEvent(upEvt);
        }})()
        """
        try:
            self.eval_js(js_dispatch)
        except Exception:
            pass

    def click_element_by_text(self, text: str, tag: str = "*") -> bool:
        """
        Locates a DOM element containing exact or partial text and clicks it.
        Uses getBoundingClientRect to dispatch a realistic mouse event at the center.
        """
        escaped_text = text.replace("'", "\\'")
        js = f"""
        (() => {{
            const elements = Array.from(document.querySelectorAll('{tag}'));
            const target = elements.find(el => {{
                const txt = el.textContent ? el.textContent.trim().toUpperCase() : '';
                return txt === '{escaped_text}'.toUpperCase() || txt.includes('{escaped_text}'.toUpperCase());
            }});
            if (!target) return null;
            const rect = target.getBoundingClientRect();
            target.scrollIntoView({{ behavior: 'instant', block: 'center' }});
            const updated = target.getBoundingClientRect();
            return {{
                x: updated.left + updated.width / 2,
                y: updated.top + updated.height / 2,
                width: updated.width,
                height: updated.height
            }};
        }})()
        """
        box = self.eval_js(js)
        if box and "x" in box and "y" in box:
            self.click_at(box["x"], box["y"])
            return True
        return False

    def close(self):
        """Closes CDP connection."""
        if self.ws:
            self.ws.close()
            self.ws = None
