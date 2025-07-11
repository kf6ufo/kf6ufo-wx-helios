import utils
import config
import sys
import importlib.machinery
import importlib.util

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


def test_send_via_aprsis_uses_daemon_queue(monkeypatch):
    items = []

    class DummyQueue:
        def put(self, frame):
            items.append(frame)

    DummyModule = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec('daemons.aprsis_client', None)
    )
    DummyModule.ENABLED = True
    DummyModule.FRAME_QUEUE = DummyQueue()
    DummyPkg = importlib.util.module_from_spec(
        importlib.machinery.ModuleSpec('daemons', None)
    )
    DummyPkg.aprsis_client = DummyModule
    monkeypatch.setitem(sys.modules, 'daemons', DummyPkg)
    monkeypatch.setitem(sys.modules, 'daemons.aprsis_client', DummyModule)
    for key in ['APRSIS_MANAGER_HOST', 'APRSIS_MANAGER_PORT', 'APRSIS_MANAGER_AUTHKEY']:
        monkeypatch.delenv(key, raising=False)
    monkeypatch.setattr(config, 'load_aprsis_config', lambda: {'enabled': True})

    def fail(*a, **k):
        raise AssertionError('socket should not be used')

    monkeypatch.setattr(utils.socket, 'create_connection', fail)

    utils.send_via_aprsis('SRC>DEST:HELLO')

    assert items == ['SRC>DEST:HELLO']

