import sys
import time
import logging
import pytest
import types
import main
import config


def test_start_daemon_modules_loads(monkeypatch):
    modules = []

    class DummyModule:
        def __init__(self, name):
            self.name = name
        def start(self):
            modules.append(self.name)
            return f"srv-{self.name}", f"thr-{self.name}"

    def fake_import(name):
        return DummyModule(name)

    monkeypatch.setattr(config, "load_daemon_modules", lambda: ["m1", "m2"])
    monkeypatch.setattr(main.importlib, "import_module", fake_import)

    result = main.start_daemon_modules()
    assert modules == ["m1", "m2"]
    assert result == [("srv-m1", "thr-m1"), ("srv-m2", "thr-m2")]


def test_main_start_and_shutdown(monkeypatch):
    servers = []
    threads = []
    procs = []

    class DummyServer:
        def __init__(self):
            self.shutdown_called = 0
            servers.append(self)
        def shutdown(self):
            self.shutdown_called += 1

    class DummyThread:
        def __init__(self):
            self.join_called = 0
            threads.append(self)
        def join(self):
            self.join_called += 1

    class DummyProc:
        def __init__(self):
            self.terminated = 0
            self.waited = 0
            procs.append(self)
        def terminate(self):
            self.terminated += 1
        def wait(self):
            self.waited += 1

    def fake_start_daemon_modules():
        return [(DummyServer(), DummyThread()), (DummyServer(), DummyThread())]

    monkeypatch.setattr(main, "start_daemon_modules", fake_start_daemon_modules)
    monkeypatch.setattr(main, "start_direwolf", lambda: DummyProc())
    monkeypatch.setattr(main, "start_rigctld", lambda *a, **k: DummyProc())
    monkeypatch.setattr(main, "run_telemetry_modules", lambda: (_ for _ in ()).throw(KeyboardInterrupt()))
    monkeypatch.setattr(main.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(main.time, "sleep", lambda t: None)
    monkeypatch.setattr(logging, "basicConfig", lambda **k: None)
    monkeypatch.setattr(config, "load_rig_config", lambda: {"enabled": True})
    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})

    argv = ["main.py", "--rig-id", "1", "--usb-num", "0", "--telemetry-interval", "1"]
    monkeypatch.setattr(sys, "argv", argv)
    with pytest.raises(KeyboardInterrupt):
        main.main()

    for s in servers:
        assert s.shutdown_called == 1
    for t in threads:
        assert t.join_called == 1
    for p in procs:
        assert p.terminated == 1
        assert p.waited == 1
