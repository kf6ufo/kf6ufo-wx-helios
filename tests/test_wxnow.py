import shared_functions as shared
from telemetry import hub_telemetry
import config


def test_send_via_kiss(monkeypatch):
    sent = []

    def fake_send(frame):
        sent.append(frame)

    monkeypatch.setattr(shared, "send_raw_via_kiss", fake_send)
    monkeypatch.setattr(
        config,
        "load_aprs_config",
        lambda: ("SRC", 0.0, 0.0, "/", "Y", ["WIDE1-1"], "DEST", "v1"),
    )

    shared.send_via_kiss("TEST")

    expected = hub_telemetry.build_ax25_frame("DEST", "SRC", ["WIDE1-1"], "TEST")
    assert sent == [expected]
