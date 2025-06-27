import utils as shared
import daemons.kiss_client as kc
import sys
import subprocess
import time
import os


def test_send_via_kiss_uses_daemon_queue(monkeypatch):
    items = []

    class DummyQueue:
        def put(self, frame):
            items.append(frame)

    monkeypatch.setattr(kc, "FRAME_QUEUE", DummyQueue())
    monkeypatch.setattr(kc, "ENABLED", True)

    def fail(*a, **k):
        raise AssertionError("socket should not be used")

    monkeypatch.setattr(shared.socket, "create_connection", fail)

    frame = b"\x01\x02"
    shared.send_via_kiss(frame)

    assert items == [frame]


def test_kiss_client_connects_to_configured_host_port(monkeypatch):
    """Verify the daemon connects using configured host and port."""

    captured = {}

    class DummySocket:
        def settimeout(self, t):
            pass

        def close(self):
            pass

        def send(self, data):
            pass

    def fake_create(addr):
        captured["addr"] = addr
        return DummySocket()

    monkeypatch.setattr(kc.socket, "create_connection", fake_create)
    monkeypatch.setattr(kc, "HOST", "5.6.7.8")
    monkeypatch.setattr(kc, "PORT", 7000)
    kc.FRAME_QUEUE = kc.queue.Queue()
    kc.FRAME_QUEUE.put(None)
    kc._stop.clear()
    kc._run()

    assert captured.get("addr") == ("5.6.7.8", 7000)


def test_subprocess_can_queue_frame(monkeypatch):
    sent = []

    class DummySocket:
        def settimeout(self, t):
            pass

        def close(self):
            pass

        def send(self, data):
            sent.append(data)

    monkeypatch.setattr(kc.socket, "create_connection", lambda a: DummySocket())
    monkeypatch.setattr(kc, "HOST", "1.2.3.4")
    monkeypatch.setattr(kc, "PORT", 9000)
    monkeypatch.setattr(kc, "ENABLED", True)

    server, thread = kc.start()
    try:
        cmd = [sys.executable, "-c", "import utils; utils.send_via_kiss(b'HI')"]
        env = os.environ.copy()
        env["PYTHONPATH"] = os.pathsep.join(
            [os.path.dirname(os.path.dirname(__file__)), env.get("PYTHONPATH", "")]
        )
        subprocess.run(cmd, env=env, check=True)
        time.sleep(0.1)
    finally:
        server.shutdown()
        thread.join()

    assert sent
