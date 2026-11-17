"""
Low-level WebSocket network transport for Chrome DevTools Protocol.

Pure Python standard library implementation adhering to RFC 6455.
Handles raw socket connections, handshakes, frame encoding, masking, and ping/pong keep-alives.
"""

import os
import socket
import struct
import base64
from typing import Optional


class WebSocketTransport:
    """
    Lightweight, zero-dependency RFC 6455 WebSocket client.
    Encapsulates raw TCP socket lifecycle and WebSocket framing.
    """

    def __init__(self, host: str, port: int, path: str, timeout: float = 10.0):
        self.host = host
        self.port = port
        self.path = path
        self.timeout = timeout
        self.sock: Optional[socket.socket] = None
        self._connected = False

    @property
    def is_connected(self) -> bool:
        """Returns True if the socket is actively connected."""
        return self._connected and self.sock is not None

    def connect(self):
        """Establishes TCP connection and performs RFC 6455 handshake."""
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

        # RFC 6455 Handshake
        key = base64.b64encode(os.urandom(16)).decode("ascii")
        handshake_req = (
            f"GET {self.path} HTTP/1.1\r\n"
            f"Host: {self.host}:{self.port}\r\n"
            "Upgrade: websocket\r\n"
            "Connection: Upgrade\r\n"
            f"Sec-WebSocket-Key: {key}\r\n"
            "Sec-WebSocket-Version: 13\r\n\r\n"
        )
        self.sock.sendall(handshake_req.encode("utf-8"))

        # Read handshake response
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
        """Encodes and sends masked text frame to the server."""
        if not self._connected or not self.sock:
            raise ConnectionError("WebSocket not connected")

        payload_bytes = payload.encode("utf-8")
        length = len(payload_bytes)

        # Masking is mandatory for client-to-server frames
        mask_key = os.urandom(4)
        b1 = 0x81  # FIN=1, opcode=1 (text frame)

        if length <= 125:
            header = struct.pack("!BB", b1, 0x80 | length)
        elif length <= 65535:
            header = struct.pack("!BBH", b1, 0x80 | 126, length)
        else:
            header = struct.pack("!BBQ", b1, 0x80 | 127, length)

        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(payload_bytes))
        self.sock.sendall(header + mask_key + masked)

    def recv_text(self) -> str:
        """Reads and decodes incoming frame payload from the server."""
        if not self._connected or not self.sock:
            raise ConnectionError("WebSocket not connected")

        # Read 2-byte frame header
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
        elif opcode == 0x9:  # Ping frame -> respond with pong
            self._send_pong(payload)
            return self.recv_text()

        return payload.decode("utf-8", errors="replace")

    def _recv_exact(self, num_bytes: int) -> bytes:
        """Helper to ensure exact number of bytes are read from socket."""
        data = bytearray()
        while len(data) < num_bytes:
            chunk = self.sock.recv(num_bytes - len(data))
            if not chunk:
                raise ConnectionResetError("Connection lost while reading from WebSocket")
            data.extend(chunk)
        return bytes(data)

    def _send_pong(self, data: bytes):
        """Sends pong control frame response (opcode 0xA)."""
        mask_key = os.urandom(4)
        length = len(data)
        b1 = 0x8A  # FIN=1, opcode=10 (pong)
        header = struct.pack("!BB", b1, 0x80 | length)
        masked = bytes(b ^ mask_key[i % 4] for i, b in enumerate(data))
        self.sock.sendall(header + mask_key + masked)

    def close(self):
        """Closes the underlying TCP socket."""
        self._connected = False
        if self.sock:
            try:
                self.sock.close()
            except Exception:
                pass
            self.sock = None

    def __enter__(self):
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()


# Backward-compatible alias
SimpleWebSocket = WebSocketTransport
