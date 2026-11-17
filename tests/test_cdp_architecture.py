"""
Unit tests for decoupled CDP architecture (Facade Pattern, Transport, Session, DOM, and Input).
"""

import json
import unittest
from unittest.mock import MagicMock, patch
from ygbot.core.cdp.transport import WebSocketTransport, SimpleWebSocket
from ygbot.core.cdp.session import CDPSession
from ygbot.core.cdp.dom import CDPDOM
from ygbot.core.cdp.input import CDPInput
from ygbot.core.cdp.client import CDPClient, BrowserDriver


class TestCDPTransport(unittest.TestCase):
    """Verifies low-level WebSocket transport framing and socket lifecycle."""

    def test_transport_initialization(self):
        transport = WebSocketTransport(host="127.0.0.1", port=9222, path="/devtools/page/1")
        self.assertEqual(transport.host, "127.0.0.1")
        self.assertEqual(transport.port, 9222)
        self.assertEqual(transport.path, "/devtools/page/1")
        self.assertFalse(transport.is_connected)

    def test_transport_send_text_unconnected_raises(self):
        transport = WebSocketTransport("127.0.0.1", 9222, "/test")
        with self.assertRaises(ConnectionError):
            transport.send_text("test")

    def test_transport_recv_text_unconnected_raises(self):
        transport = WebSocketTransport("127.0.0.1", 9222, "/test")
        with self.assertRaises(ConnectionError):
            transport.recv_text()

    def test_alias_equivalence(self):
        self.assertIs(SimpleWebSocket, WebSocketTransport)


class TestCDPSession(unittest.TestCase):
    """Verifies tab querying, session lifecycle, and JSON-RPC dispatching."""

    def setUp(self):
        self.session = CDPSession(host="127.0.0.1", port=9222)

    @patch("urllib.request.urlopen")
    def test_is_chrome_running_true(self, mock_urlopen):
        mock_resp = MagicMock()
        mock_resp.status = 200
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        self.assertTrue(self.session.is_chrome_running())

    @patch("urllib.request.urlopen")
    def test_is_chrome_running_false_on_network_error(self, mock_urlopen):
        mock_urlopen.side_effect = Exception("Connection refused")
        self.assertFalse(self.session.is_chrome_running())

    @patch("urllib.request.urlopen")
    def test_get_tabs_and_find_tab(self, mock_urlopen):
        tabs_payload = json.dumps([
            {"type": "page", "title": "Yu-Gi-Oh! Forbidden Memories", "url": "https://ygofm.com/"},
            {"type": "background_page", "title": "Extension", "url": "chrome-extension://..."},
        ]).encode("utf-8")

        mock_resp = MagicMock()
        mock_resp.read.return_value = tabs_payload
        mock_resp.__enter__.return_value = mock_resp
        mock_urlopen.return_value = mock_resp

        tabs = self.session.get_tabs()
        self.assertEqual(len(tabs), 1)
        self.assertEqual(tabs[0]["title"], "Yu-Gi-Oh! Forbidden Memories")

        # Find tab matching pattern
        tab = self.session.find_tab(["ygofm.com"])
        self.assertIsNotNone(tab)
        self.assertEqual(tab["url"], "https://ygofm.com/")

    def test_send_cmd_json_rpc(self):
        mock_transport = MagicMock()
        self.session.transport = mock_transport
        mock_transport.is_connected = True

        # Simulate receiving response for msg id 1
        mock_transport.recv_text.return_value = json.dumps({
            "id": 1,
            "result": {"value": 42}
        })

        result = self.session.send_cmd("Runtime.evaluate", {"expression": "21 * 2"})
        self.assertEqual(result, {"value": 42})
        self.assertEqual(self.session.msg_id, 2)

    def test_send_cmd_raises_on_error_response(self):
        mock_transport = MagicMock()
        self.session.transport = mock_transport
        mock_transport.is_connected = True

        mock_transport.recv_text.return_value = json.dumps({
            "id": 1,
            "error": {"message": "Invalid parameter"}
        })

        with self.assertRaises(RuntimeError) as ctx:
            self.session.send_cmd("Page.navigate", {})
        self.assertIn("Invalid parameter", str(ctx.exception))


class TestCDPDOMAndInput(unittest.TestCase):
    """Verifies CDPDOM and CDPInput subsystem interactions."""

    def setUp(self):
        self.mock_session = MagicMock()
        self.dom = CDPDOM(self.mock_session)
        self.input_subsystem = CDPInput(self.mock_session, self.dom)

    def test_eval_js(self):
        self.mock_session.send_cmd.return_value = {"result": {"value": "Dark Magician"}}
        val = self.dom.eval_js("document.title")
        self.assertEqual(val, "Dark Magician")
        self.mock_session.send_cmd.assert_called_once_with(
            "Runtime.evaluate",
            {"expression": "document.title", "returnByValue": True, "awaitPromise": True}
        )

    def test_update_viewport_size_metrics(self):
        self.mock_session.send_cmd.return_value = {
            "cssLayoutViewport": {"clientWidth": 1280, "clientHeight": 720}
        }
        w, h = self.dom.update_viewport_size()
        self.assertEqual(w, 1280)
        self.assertEqual(h, 720)
        self.assertEqual(self.dom.viewport_width, 1280)
        self.assertEqual(self.dom.viewport_height, 720)

    def test_click_at_dispatches_mouse_events(self):
        self.input_subsystem.click_at(500, 300, delay=0.0)
        calls = self.mock_session.send_cmd.call_args_list
        self.assertEqual(len(calls), 2)
        # Mouse pressed
        self.assertEqual(calls[0].args[0], "Input.dispatchMouseEvent")
        self.assertEqual(calls[0].args[1]["type"], "mousePressed")
        self.assertEqual(calls[0].args[1]["x"], 500)
        # Mouse released
        self.assertEqual(calls[1].args[0], "Input.dispatchMouseEvent")
        self.assertEqual(calls[1].args[1]["type"], "mouseReleased")

    def test_click_percent_scales_coordinates(self):
        self.dom.viewport_width = 1000
        self.dom.viewport_height = 500
        self.input_subsystem.click_percent(0.5, 0.2, delay=0.0)
        calls = self.mock_session.send_cmd.call_args_list
        self.assertEqual(calls[0].args[1]["x"], 500)
        self.assertEqual(calls[0].args[1]["y"], 100)

    def test_send_key_escape_and_enter(self):
        self.input_subsystem.send_key("Enter", delay=0.0)
        methods = [c.args[0] for c in self.mock_session.send_cmd.call_args_list]
        self.assertIn("Input.dispatchKeyEvent", methods)

        self.mock_session.send_cmd.reset_mock()
        self.input_subsystem.send_key("Escape", delay=0.0)
        call_params = [c.args[1] for c in self.mock_session.send_cmd.call_args_list if c.args[0] == "Input.dispatchKeyEvent"]
        self.assertTrue(any(p.get("windowsVirtualKeyCode") == 27 for p in call_params))


class TestCDPClientFacade(unittest.TestCase):
    """Verifies the Facade pattern implementation in CDPClient."""

    def test_facade_subsystem_delegation(self):
        client = CDPClient(host="localhost", port=9222)

        # Check subsystems instantiated
        self.assertIsInstance(client.session, CDPSession)
        self.assertIsInstance(client.dom, CDPDOM)
        self.assertIsInstance(client.input, CDPInput)

        # Verify alias
        self.assertIs(BrowserDriver, CDPClient)

        # Mock subsystems and verify delegation
        client.session = MagicMock()
        client.dom = MagicMock()
        client.input = MagicMock()

        # is_chrome_running
        client.session.is_chrome_running.return_value = True
        self.assertTrue(client.is_chrome_running())
        client.session.is_chrome_running.assert_called_once()

        # get_tabs
        client.get_tabs()
        client.session.get_tabs.assert_called_once()

        # eval_js
        client.dom.eval_js.return_value = "hello"
        self.assertEqual(client.eval_js("1+1"), "hello")
        client.dom.eval_js.assert_called_once_with("1+1")

        # click_at
        client.click_at(10, 20, delay=0.01)
        client.input.click_at.assert_called_once_with(10, 20, delay=0.01)

        # click_percent
        client.click_percent(0.1, 0.2, delay=0.02)
        client.input.click_percent.assert_called_once_with(0.1, 0.2, delay=0.02)

        # send_key
        client.send_key("ArrowDown", delay=0.03)
        client.input.send_key.assert_called_once_with("ArrowDown", delay=0.03)

        # close
        client.close()
        client.session.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
