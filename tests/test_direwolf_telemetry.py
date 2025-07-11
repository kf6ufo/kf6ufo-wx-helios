import pytest

pytest.importorskip("psutil")

import telemetry.direwolf_telemetry as dw
import utils as shared
import config


def test_parse_metrics():
    line = "T: busy=12.5% cd=0 rcvq=3(0.0) sendq=2(0.0)"
    result = dw.parse_metrics(line)
    assert result == {"busy": 12.5, "rcvq": 3, "sendq": 2}


def test_read_metrics_directory(tmp_path):
    old = tmp_path / "old.log"
    old.write_text("no metrics here\n")
    import time
    time.sleep(0.01)
    new = tmp_path / "new.log"
    new.write_text(
        "noise\nT: busy=12.5% cd=0 rcvq=4(0.0) sendq=3(0.0)\nmore\n"
    )
    result = dw.read_metrics(tmp_path)
    assert result == {"busy": 12.5, "rcvq": 4, "sendq": 3}


def test_kiss_frame_generation(monkeypatch):
    metrics = {"busy": 1.0, "rcvq": 2, "sendq": 3}

    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})
    monkeypatch.setattr(dw, "read_metrics", lambda path=None: metrics)
    monkeypatch.setattr(
        config,
        "load_aprs_config",
        lambda *a, **k: ("SRC-1", 10.0, -100.0, "/", "Y", ["WIDE1-1"], "DEST", "v1"),
    )

    sent = []

    def fake_send(frame):
        sent.append(frame)

    monkeypatch.setattr(shared, "send_via_kiss", fake_send)

    dw.main([])

    info = dw.build_aprs_info(10.0, -100.0, "/", "Y", "v1", metrics)
    expected = shared.build_ax25_frame("DEST", "SRC-2", ["WIDE1-1"], info)

    assert sent and sent[0] == expected
    assert info == "T#000,010,002,003,000,000,00000000 ver=v1"


def test_zero_frame_when_no_metrics(monkeypatch):
    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})
    monkeypatch.setattr(dw, "read_metrics", lambda path=None: None)
    monkeypatch.setattr(
        config,
        "load_aprs_config",
        lambda *a, **k: ("SRC-1", 10.0, -100.0, "/", "Y", ["WIDE1-1"], "DEST", "v1"),
    )

    sent = []

    def fake_send(frame):
        sent.append(frame)

    monkeypatch.setattr(shared, "send_via_kiss", fake_send)

    dw.main([])

    info = dw.build_aprs_info(10.0, -100.0, "/", "Y", "v1", {})
    expected = shared.build_ax25_frame("DEST", "SRC-2", ["WIDE1-1"], info)

    assert sent and sent[0] == expected
    assert info == "T#000,000,000,000,000,000,00000000 ver=v1"
