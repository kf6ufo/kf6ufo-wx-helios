import logging
import main
import config


def test_missing_direwolf_logs_error(monkeypatch, tmp_path, caplog):
    monkeypatch.setattr(main, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(config, "load_direwolf_config", lambda: {"enabled": True})
    # provide template so start_direwolf can copy it
    (tmp_path / "direwolf.conf.template").write_text("")
    with caplog.at_level(logging.ERROR):
        proc = main.start_direwolf()
    assert proc is None
    assert any("Direwolf binary not found" in r.message for r in caplog.records)
