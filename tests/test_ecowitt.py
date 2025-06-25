import importlib.util
from pathlib import Path
from datetime import datetime, timedelta
import pytest

MODULE_PATH = Path(__file__).resolve().parent.parent / "daemons" / "ecowitt_listener.py"

def load_module():
    spec = importlib.util.spec_from_file_location("ecowitt_listener", MODULE_PATH)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

@pytest.mark.parametrize("temp,expected", [
    (-5, "t-05"),
    (0, "t000"),
    (100, "t100"),
    (199, "t199"),
    (250, "t199"),
])
def test_temperature_field(temp, expected):
    mod = load_module()
    mod.update_rain_24h = lambda p: 0
    params = {
        "winddir": "0",
        "windspeedmph": "0",
        "windgustmph": "0",
        "tempf": str(temp),
        "hourlyrainin": "0",
        "eventrainin": "0",
        "humidity": "50",
        "baromrelin": "30",
        "dateutc": "2020-01-01 00:00:00",
    }
    frame = mod.ecowitt_to_aprs(params)
    assert expected in frame

def test_update_rain_24h_accumulation_and_cleanup():
    """Verify 24‑h totals over a simulated 48‑h period."""
    mod = load_module()
    mod.RAIN_CACHE.clear()

    start = datetime(2020, 1, 1, 0, 0, 0)
    for i in range(48):
        ts = (start + timedelta(hours=i)).strftime("%Y-%m-%d %H:%M:%S")
        p = {"dateutc": ts, "hourlyrainin": "0.10"}
        val = mod.update_rain_24h(p)
        hours = min(i + 1, 24)
        assert len(mod.RAIN_CACHE) == hours
        assert val == hours * 10

def test_update_rain_24h_same_hour_replaces():
    mod = load_module()
    mod.RAIN_CACHE.clear()
    p1 = {"dateutc": "2020-01-01 01:10:00", "hourlyrainin": "0.10"}
    assert mod.update_rain_24h(p1) == 10
    assert len(mod.RAIN_CACHE) == 1

    p2 = {"dateutc": "2020-01-01 01:50:00", "hourlyrainin": "0.20"}
    assert mod.update_rain_24h(p2) == 20
    assert len(mod.RAIN_CACHE) == 1
