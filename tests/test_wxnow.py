import shared_functions as shared


def test_send_via_wxnow(tmp_path, monkeypatch):
    dest = tmp_path / "wxnow.txt"
    monkeypatch.setattr(shared, "WXNOW", dest)
    shared.send_via_wxnow("TESTFRAME")
    lines = dest.read_text().splitlines()
    assert lines[-1] == "TESTFRAME"
