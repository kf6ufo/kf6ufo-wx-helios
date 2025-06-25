import configparser
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "wx-helios.conf"

_config = None

def _get_config():
    global _config
    if _config is None:
        parser = configparser.ConfigParser()
        parser.read(CONFIG_PATH)
        _config = parser
    return _config

def load_aprs_config():
    cfg = _get_config()
    aprs = cfg["APRS"]
    callsign = aprs["callsign"]
    latitude = float(aprs["latitude"])
    longitude = float(aprs["longitude"])
    symbol_table_raw = aprs.get("symbol_table", "primary").strip().lower()
    symbol_table = "/" if symbol_table_raw == "primary" else "\\"
    symbol = aprs["symbol"]
    path = [p.strip() for p in aprs.get("path", "").split(",") if p.strip()]
    destination = aprs.get("destination", "APZ001")
    version = aprs.get("version", "v5")
    return callsign, latitude, longitude, symbol_table, symbol, path, destination, version

def load_ecowitt_config():
    cfg = _get_config()
    if "ECOWITT" not in cfg:
        return {"port": 8080, "path": "/data/report", "lat": "3742.12N", "lon": "10854.32W"}
    eco = cfg["ECOWITT"]
    return {
        "port": int(eco.get("port", 8080)),
        "path": eco.get("path", "/data/report"),
        "lat": eco.get("lat", "3742.12N"),
        "lon": eco.get("lon", "10854.32W"),
    }
