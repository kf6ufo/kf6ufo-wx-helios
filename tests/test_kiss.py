import unittest
from unittest.mock import patch
import pytest

# Skip these tests entirely if psutil isn't available since hub_telemetry
# depends on it at import time.
pytest.importorskip("psutil")

import utils as shared

class DummySocket:
    def __init__(self):
        self.sent = b''
    def send(self, data):
        self.sent += data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


def test_send_via_kiss(monkeypatch):
    """Verify frames are sent over a socket."""
    dummy = DummySocket()
    with patch('socket.create_connection', return_value=dummy):
        shared.send_via_kiss(b'TEST')
    assert dummy.sent == b'\xC0\x00TEST\xC0'

class TestKissEscaping(unittest.TestCase):
    def _run_send(self, payload):
        dummy = DummySocket()
        with patch('socket.create_connection', return_value=dummy):
            shared.send_via_kiss(payload)
        return dummy.sent

    def test_no_escape(self):
        data = b'\x01\x02\x03'
        expected = b'\xC0\x00\x01\x02\x03\xC0'
        self.assertEqual(self._run_send(data), expected)

    def test_escape_c0(self):
        data = b'\xC0'
        expected = b'\xC0\x00\xDB\xDC\xC0'
        self.assertEqual(self._run_send(data), expected)

    def test_escape_db(self):
        data = b'\xDB'
        expected = b'\xC0\x00\xDB\xDD\xC0'
        self.assertEqual(self._run_send(data), expected)

    def test_escape_mixed(self):
        data = b'\xC0\xDB'
        expected = b'\xC0\x00\xDB\xDC\xDB\xDD\xC0'
        self.assertEqual(self._run_send(data), expected)

if __name__ == '__main__':
    unittest.main()
