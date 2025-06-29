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

    hub_defs = defs.hub_definitions("DEST")
    dw_defs = defs.direwolf_definitions("DEST")
    infos = hub_defs + dw_defs
    expected = []
    for i, info in enumerate(infos):
        callsign = "SRC-1" if i < len(hub_defs) else "SRC-2"
        expected.append(shared.build_ax25_frame("DEST", callsign, ["W"], info))
    assert sent == expected

    prefix = ":" + "DEST".ljust(9)[:9] + ":"
    assert infos[3].startswith(prefix + "BITS.11000000")
    assert infos[7].startswith(prefix + "BITS.00000000")
    for info in infos:
        assert info.startswith(":")
