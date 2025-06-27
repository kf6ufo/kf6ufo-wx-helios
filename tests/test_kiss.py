import unittest
from unittest.mock import patch
import pytest

# Skip these tests entirely if psutil isn't available since hub_telemetry
# depends on it at import time.
pytest.importorskip("psutil")

import shared_functions as shared

class DummySocket:
    def __init__(self):
        self.sent = b''
    def send(self, data):
        self.sent += data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

class TestKissEscaping(unittest.TestCase):
    def _run_send(self, payload):
        dummy = DummySocket()
        with patch('socket.create_connection', return_value=dummy):
            shared.send_raw_via_kiss(payload)
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
