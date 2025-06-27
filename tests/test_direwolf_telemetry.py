import pytest
from unittest.mock import patch

pytest.importorskip("psutil")

import telemetry.direwolf_telemetry as dw
from telemetry import hub_telemetry
import shared_functions as shared
import config


def test_parse_metrics():
    line = "T: busy=12.5% cd=0 rcvq=3(0.0) sendq=2(0.0)"
    result = dw.parse_metrics(line)
    assert result == {"busy": 12.5, "rcvq": 3, "sendq": 2}


def test_kiss_frame_generation(monkeypatch):
    metrics = {"busy": 1.0, "rcvq": 2, "sendq": 3}

    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})
    monkeypatch.setattr(dw, "read_metrics", lambda path=None: metrics)
    monkeypatch.setattr(
        config,
        "load_aprs_config",
        lambda: ("SRC-1", 10.0, -100.0, "/", "Y", ["WIDE1-1"], "DEST", "v1"),
    )

    sent = []

    def fake_send(frame):
        sent.append(frame)

    monkeypatch.setattr(shared, "send_raw_via_kiss", fake_send)

    dw.main([])

    info = dw.build_aprs_info(10.0, -100.0, "/", "Y", "v1", metrics)
    expected = hub_telemetry.build_ax25_frame("DEST", "SRC-1", ["WIDE1-1"], info)

    assert sent and sent[0] == expected
