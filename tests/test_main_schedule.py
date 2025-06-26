import sys
import logging
import warnings
import pytest

import main
import config

# croniter versions < 1.4 trigger DeprecationWarnings on Python 3.12 when
# using ``datetime.utcfromtimestamp`` internally. Silence these warnings so
# the test output is clean.
warnings.filterwarnings(
    "ignore",
    category=DeprecationWarning,
    module=r"^croniter",
)


def test_scheduler_runs_at_cron_times(monkeypatch):
    calls = []
    current = 0

    def fake_time():
        return current

    def fake_sleep(t):
        nonlocal current
        current += t

    def fake_run(name):
        calls.append((name, current))
        if len(calls) >= 3:
            raise KeyboardInterrupt()

    monkeypatch.setattr(main.time, "time", fake_time)
    monkeypatch.setattr(main.time, "sleep", fake_sleep)
    monkeypatch.setattr(main.signal, "signal", lambda *a, **k: None)
    monkeypatch.setattr(logging, "basicConfig", lambda **k: None)
    monkeypatch.setattr(main, "start_direwolf", lambda: None)
    monkeypatch.setattr(main, "start_rigctld", lambda *a, **k: None)
    monkeypatch.setattr(main, "start_daemon_modules", lambda: [])
    monkeypatch.setattr(config, "load_rig_config", lambda: {"enabled": False})
    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": False})
    monkeypatch.setattr(config, "load_telemetry_modules", lambda: ["m1", "m2"])
    monkeypatch.setattr(
        config,
        "load_telemetry_schedules",
        lambda: {"m1": "*/2 * * * *", "m2": "*/5 * * * *"},
    )
    monkeypatch.setattr(main, "run_telemetry_module", fake_run)

    argv = ["main.py", "--rig-id", "1", "--usb-num", "0", "--telemetry-interval", "60"]
    monkeypatch.setattr(sys, "argv", argv)

    with pytest.raises(KeyboardInterrupt):
        main.main()

    assert calls == [
        ("m1", 120),
        ("m1", 240),
        ("m2", 300),
    ]

