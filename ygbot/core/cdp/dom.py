"""
CDP DOM & Layout Subsystem.

Encapsulates layout viewport sizing, JavaScript expression evaluation,
and DOM element query helpers via Chrome DevTools Protocol.
"""

from typing import Optional, Dict, Any, Tuple, Callable


class CDPDOM:
    """
    Subsystem responsible for JavaScript evaluation, viewport dimension tracking,
    and DOM element bounding box queries.
    """

    def __init__(self, session):
        self.session = session
        self.viewport_width: int = 1920
        self.viewport_height: int = 1080

    def eval_js(self, expr: str, return_by_value: bool = True, await_promise: bool = True) -> Any:
        """Evaluates a JavaScript expression in the tab execution context."""
        res = self.session.send_cmd("Runtime.evaluate", {
            "expression": expr,
            "returnByValue": return_by_value,
            "awaitPromise": await_promise,
        })
        result_obj = res.get("result", {})
        return result_obj.get("value")

    def update_viewport_size(self) -> Tuple[int, int]:
        """Fetches layout viewport size via Page.getLayoutMetrics with JS fallback."""
        try:
            metrics = self.session.send_cmd("Page.getLayoutMetrics")
            viewport = metrics.get("cssLayoutViewport", {})
            self.viewport_width = int(viewport.get("clientWidth", 1920))
            self.viewport_height = int(viewport.get("clientHeight", 1080))
        except Exception:
            dims = self.eval_js("[window.innerWidth, window.innerHeight]")
            if dims and len(dims) == 2:
                self.viewport_width = int(dims[0])
                self.viewport_height = int(dims[1])

        return self.viewport_width, self.viewport_height

    def find_element_bounds_by_text(self, text: str, tag: str = "*") -> Optional[Dict[str, float]]:
        """
        Locates a DOM element containing specified text and returns its center coordinates and size.
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
            target.scrollIntoView({{ behavior: 'instant', block: 'center' }});
            const rect = target.getBoundingClientRect();
            return {{
                x: rect.left + rect.width / 2,
                y: rect.top + rect.height / 2,
                width: rect.width,
                height: rect.height
            }};
        }})()
        """
        box = self.eval_js(js)
        if box and isinstance(box, dict) and "x" in box and "y" in box:
            return box
        return None
