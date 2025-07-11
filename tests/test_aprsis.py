import utils
import config
from unittest.mock import patch

class DummySocket:
    def __init__(self):
        self.sent = b""
    def sendall(self, data):
        self.sent += data
    def __enter__(self):
        return self
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def test_send_via_aprsis(monkeypatch):
    dummy = DummySocket()
    captured = {}
    def fake_create(addr, timeout=None):
        captured['addr'] = addr
        captured['timeout'] = timeout
        return dummy

    monkeypatch.setattr(utils.socket, 'create_connection', fake_create)
    monkeypatch.setattr(config, 'load_aprsis_config', lambda: {
        'enabled': True,
        'callsign': 'N0CALL',
        'passcode': '11111',
        'server': 'host',
        'port': 2020,
        'timeout': 3,
    })

    utils.send_via_aprsis('SRC>DEST:HELLO')

    assert captured['addr'] == ('host', 2020)
    assert captured['timeout'] == 3
    expected = b"user N0CALL pass 11111 vers wx-helios 0\r\nSRC>DEST:HELLO\r\n"
    assert dummy.sent == expected

