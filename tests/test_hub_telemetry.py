import pytest
pytest.importorskip("psutil")

import telemetry.hub_telemetry as hub
import utils as shared
import config


def test_hub_telemetry_frame(monkeypatch):
    tele = (25.2, 52.0, 3, 91.0, 40.0, 7, 9)
    monkeypatch.setattr(hub, "get_laptop_telemetry", lambda: tele)
    monkeypatch.setattr(config, "load_hubtelemetry_config", lambda: {"enabled": True})
    monkeypatch.setattr(
        config,
        "load_aprs_config",
        lambda *a, **k: ("SRC-1", 0.0, 0.0, "/", "T", ["WIDE"], "DEST", "v2"),
    )

    sent = []
    monkeypatch.setattr(shared, "send_via_kiss", lambda frame: sent.append(frame))

    hub.main([])

    info = hub.build_aprs_info(0.0, 0.0, "/", "T", "v2", *tele)
    expected = shared.build_ax25_frame("DEST", "SRC-1", ["WIDE"], info)

    assert sent and sent[0] == expected
    assert info == "T#000,025,052,003,007,009,01000000 ver=v2"
