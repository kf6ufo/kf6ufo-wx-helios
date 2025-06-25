import config


def write_config(tmp_path, text, monkeypatch):
    path = tmp_path / "wx-helios.conf"
    path.write_text(text)
    monkeypatch.setattr(config, "CONFIG_PATH", path)
    config._config = None
    return path


def test_daemons_default(tmp_path, monkeypatch):
    write_config(tmp_path, "", monkeypatch)
    assert config.load_daemon_modules() == ["daemons.ecowitt_listener"]


def test_daemons_disabled(tmp_path, monkeypatch):
    write_config(tmp_path, "[DAEMONS]\nenabled = no\nmodules = a,b\n", monkeypatch)
    assert config.load_daemon_modules() == []


def test_daemons_custom(tmp_path, monkeypatch):
    write_config(tmp_path, "[DAEMONS]\nmodules = foo , bar\n", monkeypatch)
    assert config.load_daemon_modules() == ["foo", "bar"]


def test_telemetry_custom(tmp_path, monkeypatch):
    write_config(tmp_path, "[TELEMETRY]\nmodules = t1, t2\n", monkeypatch)
    assert config.load_telemetry_modules() == ["t1", "t2"]
