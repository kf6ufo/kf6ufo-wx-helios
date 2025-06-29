import utils


def test_callsign_with_offset():
    assert utils.callsign_with_offset("N0CALL-10", 0) == "N0CALL-10"
    assert utils.callsign_with_offset("N0CALL-10", 1) == "N0CALL-11"
    assert utils.callsign_with_offset("CALL", 2) == "CALL-2"

