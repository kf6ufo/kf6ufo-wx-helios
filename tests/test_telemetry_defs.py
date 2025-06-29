import telemetry.telemetry_defs as defs
import utils as shared
import config


def test_def_frames(monkeypatch):
    monkeypatch.setattr(config, "load_hubtelemetry_config", lambda: {"enabled": True})
    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})

    def fake_aprs(section=None):
        return ("SRC-1", 0.0, 0.0, "/", "T", ["W"], "DEST", "v")

    monkeypatch.setattr(config, "load_aprs_config", fake_aprs)

    sent = []
    monkeypatch.setattr(shared, "send_via_kiss", lambda frame: sent.append(frame))

    defs.main([])

    infos = defs.hub_definitions() + defs.direwolf_definitions()
    expected = [shared.build_ax25_frame("DEST", "SRC-1", ["W"], info) for info in infos]

    assert sent == expected
