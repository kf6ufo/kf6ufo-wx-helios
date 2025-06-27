import utils as shared
import daemons.kiss_client as kc


def test_send_via_kiss_uses_daemon_queue(monkeypatch):
    items = []

    class DummyQueue:
        def put(self, frame):
            items.append(frame)

    monkeypatch.setattr(kc, "FRAME_QUEUE", DummyQueue())
    monkeypatch.setattr(kc, "ENABLED", True)
    monkeypatch.setattr(kc, "_socket", object())

    def fail(*a, **k):
        raise AssertionError("socket should not be used")

    monkeypatch.setattr(shared.socket, "create_connection", fail)

    frame = b"\x01\x02"
    shared.send_via_kiss(frame)

    assert items == [frame]
