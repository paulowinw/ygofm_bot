"""
CDP Input Subsystem.

Dispatches physical mouse clicks and keyboard key events via Chrome DevTools Protocol.
Provides coordinate scaling, physical key event modeling, and synthetic DOM fallbacks.
"""

import time
from typing import Optional, Dict, Any
from ..utils import log


class CDPInput:
    """
    Subsystem responsible for mouse interaction and keyboard dispatching
    via the Input domain in Chrome DevTools Protocol.
    """

    def __init__(self, session, dom):
        self.session = session
        self.dom = dom

    def click_at(self, x: float, y: float, delay: float = 0.05, button: str = "left", click_count: int = 1):
        """Simulates physical mouse click (press + release) at exact pixel coordinates (x, y)."""
        self.session.send_cmd("Input.dispatchMouseEvent", {
            "type": "mousePressed",
            "x": int(x),
            "y": int(y),
            "button": button,
            "clickCount": click_count,
        })
        time.sleep(delay)
        self.session.send_cmd("Input.dispatchMouseEvent", {
            "type": "mouseReleased",
            "x": int(x),
            "y": int(y),
            "button": button,
            "clickCount": click_count,
        })

    def click_percent(self, x_pct: float, y_pct: float, delay: float = 0.05):
        """Simulates mouse click at relative percentage coordinates (0.0 to 1.0)."""
        x = x_pct * self.dom.viewport_width
        y = y_pct * self.dom.viewport_height
        self.click_at(x, y, delay)

    def click_element_by_text(self, text: str, tag: str = "*", delay: float = 0.05) -> bool:
        """Locates a DOM element by text content and clicks its center coordinates."""
        bounds = self.dom.find_element_bounds_by_text(text, tag=tag)
        if bounds and "x" in bounds and "y" in bounds:
            self.click_at(bounds["x"], bounds["y"], delay=delay)
            return True
        return False

    def send_key(self, key_name: str, delay: float = 0.05):
        """
        Dispatches physical keyboard key press (keydown + keyup) via CDP.
        Compatible with WebGL Canvas, Emulators, and standard DOM keyboard event listeners.
        """
        key_defs = {
            "ArrowDown": {"key": "ArrowDown", "code": "ArrowDown", "windowsVirtualKeyCode": 40, "nativeVirtualKeyCode": 40},
            "ArrowUp": {"key": "ArrowUp", "code": "ArrowUp", "windowsVirtualKeyCode": 38, "nativeVirtualKeyCode": 38},
            "ArrowLeft": {"key": "ArrowLeft", "code": "ArrowLeft", "windowsVirtualKeyCode": 37, "nativeVirtualKeyCode": 37},
            "ArrowRight": {"key": "ArrowRight", "code": "ArrowRight", "windowsVirtualKeyCode": 39, "nativeVirtualKeyCode": 39},
            "Enter": {"key": "Enter", "code": "Enter", "windowsVirtualKeyCode": 13, "nativeVirtualKeyCode": 13, "text": "\r"},
            "Escape": {"key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27, "nativeVirtualKeyCode": 27},
            "Esc": {"key": "Escape", "code": "Escape", "windowsVirtualKeyCode": 27, "nativeVirtualKeyCode": 27},
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

            self.session.send_cmd("Input.dispatchKeyEvent", down_params)

            if "text" in key_info and key_info["text"]:
                self.session.send_cmd("Input.dispatchKeyEvent", {
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
            self.session.send_cmd("Input.dispatchKeyEvent", up_params)
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
            self.dom.eval_js(js_dispatch)
        except Exception:
            pass
