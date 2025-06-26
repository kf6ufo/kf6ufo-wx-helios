import configparser
from pathlib import Path

CONFIG_PATH = Path(__file__).resolve().parent / "wx-helios.conf"

# Default TCP port for rigctld. This value must match the port used in
# ``direwolf.conf.template`` on the ``PTT RIG`` line.
RIGCTLD_PORT = 4534

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
        return {
            "port": 8080,
            "path": "/data/report",
            "enabled": True,
        }
    eco = cfg["ECOWITT"]
    return {
        "port": int(eco.get("port", 8080)),
        "path": eco.get("path", "/data/report"),
        "enabled": eco.getboolean("enabled", True),
    }


def load_hubtelemetry_config():
    cfg = _get_config()
    section = "HUBTELEMETRY"
    if section not in cfg:
        return {"enabled": True}
    hub = cfg[section]
    return {"enabled": hub.getboolean("enabled", True)}


def _load_module_list(section, default):
    cfg = _get_config()
    if section not in cfg:
        return default
    sec = cfg[section]
    if not sec.getboolean("enabled", True):
        return []
    modules = [m.strip() for m in sec.get("modules", ",".join(default)).split(",") if m.strip()]
    return modules


def load_daemon_modules():
    """Return list of enabled daemon module names."""
    return _load_module_list("DAEMONS", ["daemons.ecowitt_listener"])


def load_telemetry_modules():
    """Return list of enabled telemetry module names."""
    return _load_module_list("TELEMETRY", ["telemetry.hub_telemetry"])


def load_telemetry_schedules():
    """Return mapping of telemetry module names to cron expressions."""
    cfg = _get_config()
    section = "TELEMETRY_SCHEDULES"
    if section not in cfg:
        return {}
    sec = cfg[section]
    return {name: expr for name, expr in sec.items()}


def load_direwolf_config():
    cfg = _get_config()
    section = "DIREWOLF"
    if section not in cfg:
        return {"enabled": True}
    dw = cfg[section]
    return {"enabled": dw.getboolean("enabled", True)}


def load_rig_config():
    cfg = _get_config()
    section = "RIG"
    if section not in cfg:
        return {"enabled": True}
    rig = cfg[section]
    result = {"enabled": rig.getboolean("enabled", True)}
    if "rig_id" in rig:
        result["rig_id"] = int(rig.get("rig_id", 0))
    if "usb_num" in rig:
        result["usb_num"] = int(rig.get("usb_num", 0))
    result["port"] = int(rig.get("port", RIGCTLD_PORT))
    return result
