import config


def write_config(tmp_path, text, monkeypatch):
    path = tmp_path / "wx-helios.conf"
    path.write_text(text)
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    config._config = None
    return path


def test_daemons_default(tmp_path, monkeypatch):
    write_config(tmp_path, "", monkeypatch)
    assert config.load_daemon_modules() == [
        "daemons.ecowitt_listener",
        "daemons.kiss_client",
    ]


def test_daemons_disabled(tmp_path, monkeypatch):
    write_config(tmp_path, "[DAEMONS]\nenabled = no\nmodules = a,b\n", monkeypatch)
    assert config.load_daemon_modules() == []


def test_daemons_custom(tmp_path, monkeypatch):
    write_config(tmp_path, "[DAEMONS]\nmodules = foo , bar\n", monkeypatch)
    assert config.load_daemon_modules() == ["foo", "bar"]


def test_telemetry_custom(tmp_path, monkeypatch):
    write_config(tmp_path, "[TELEMETRY]\nmodules = t1, t2\n", monkeypatch)
    assert config.load_telemetry_modules() == ["t1", "t2"]


def test_telemetry_schedules_default(tmp_path, monkeypatch):
    write_config(tmp_path, "", monkeypatch)
    assert config.load_telemetry_schedules() == {}


def test_telemetry_schedules_values(tmp_path, monkeypatch):
    write_config(
        tmp_path,
        "[TELEMETRY_SCHEDULES]\nfoo = 0 * * * *\nbar = */5 * * * *\n",
        monkeypatch,
    )
    assert config.load_telemetry_schedules() == {
        "foo": "0 * * * *",
        "bar": "*/5 * * * *",
    }


def test_rig_config_with_baud(tmp_path, monkeypatch):
    conf = """[RIG]
rig_id = 1
usb_num = 2
baud = 4800
port = 9999
"""
    write_config(tmp_path, conf, monkeypatch)
    cfg = config.load_rig_config()
    assert cfg == {
        "enabled": True,
        "rig_id": 1,
        "usb_num": 2,
        "baud": 4800,
        "port": 9999,
    }


def test_aprsis_default(tmp_path, monkeypatch):
    write_config(tmp_path, "", monkeypatch)
    assert config.load_aprsis_config() == {"enabled": False}


def test_aprsis_values(tmp_path, monkeypatch):
    conf = (
        "[APRS]\ncallsign = N0CALL\nlatitude = 0\nlongitude = 0\n"
        "[APRS_IS]\nenabled = yes\npasscode = 2222\nserver = test.example\n"
        "port = 1234\ntimeout = 5\n"
    )
    write_config(tmp_path, conf, monkeypatch)
    cfg = config.load_aprsis_config()
    assert cfg == {
        "enabled": True,
        "callsign": "N0CALL",
        "passcode": "2222",
        "server": "test.example",
        "port": 1234,
        "timeout": 5.0,
    }
