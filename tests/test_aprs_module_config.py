import config


def write_config(tmp_path, text, monkeypatch):
    path = tmp_path / "wx-helios.conf"
    path.write_text(text)
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    config._config = None
    return path


def test_aprs_module_override(tmp_path, monkeypatch):
    cfg_text = """
[APRS]
callsign = N0CALL-9
latitude = 1
longitude = 2
symbol_table = primary
symbol = T
path = W1-1

[ECOWITT]
symbol_table = secondary
symbol = W
digipeater_path = W2-2,W3-3
"""
    write_config(tmp_path, cfg_text, monkeypatch)
    # Default section
    base = config.load_aprs_config()
    assert base[3] == "/"
    assert base[4] == "T"
    assert base[5] == ["W1-1"]
    # Module override
    mod = config.load_aprs_config("ECOWITT")
    assert mod[3] == "\\"
    assert mod[4] == "W"
    assert mod[5] == ["W2-2", "W3-3"]

