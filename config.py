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

_UNICODE_MINUS_TRANSLATION = str.maketrans({
    "\u2212": "-",  # minus sign
    "\u2013": "-",  # en dash
    "\u2014": "-",  # em dash
    "\u2015": "-",  # horizontal bar
})


def _parse_float(value: str) -> float:
    """Parse a float while normalising Unicode minus characters."""

    if isinstance(value, str):
        value = value.translate(_UNICODE_MINUS_TRANSLATION)
    return float(value)


def load_aprs_config(section: str | None = None):
    """Return APRS configuration, optionally overridden per module.

    Parameters
    ----------
    section : str or None
        Optional configuration section providing module specific overrides.

    Returns
    -------
    tuple
        ``(callsign, latitude, longitude, symbol_table, symbol, path, destination, version)``
    """

    cfg = _get_config()
    aprs = cfg["APRS"]

    callsign = aprs["callsign"]
    latitude = _parse_float(aprs["latitude"])
    longitude = _parse_float(aprs["longitude"])

    symbol_table_raw = aprs.get("symbol_table", "primary").strip().lower()
    symbol_table = "/" if symbol_table_raw == "primary" else "\\"
    symbol = aprs.get("symbol", "_")
    path = [p.strip() for p in aprs.get("path", "").split(",") if p.strip()]

    if section and section in cfg:
        sec = cfg[section]
        sym_raw = sec.get("symbol_table", symbol_table_raw).strip().lower()
        symbol_table = "/" if sym_raw == "primary" else "\\"
        symbol = sec.get("symbol", symbol)
        # support either digipeater_path or aprs_path for clarity
        path_key = "digipeater_path" if "digipeater_path" in sec else "aprs_path"
        if path_key in sec:
            path = [p.strip() for p in sec.get(path_key, "").split(",") if p.strip()]

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
    return _load_module_list(
        "DAEMONS",
        ["daemons.ecowitt_listener", "daemons.kiss_client", "daemons.aprsis_client"],
    )


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


def load_kiss_client_config():
    cfg = _get_config()
    section = "KISS_CLIENT"
    if section not in cfg:
        return {"enabled": False, "host": "127.0.0.1", "port": 8001}
    kc = cfg[section]
    return {
        "enabled": kc.getboolean("enabled", True),
        "host": kc.get("host", "127.0.0.1"),
        "port": int(kc.get("port", 8001)),
    }


def load_aprsis_config():
    cfg = _get_config()
    section = "APRS_IS"
    if section not in cfg:
        return {"enabled": False}
    sec = cfg[section]
    callsign = sec.get("callsign", cfg["APRS"].get("callsign"))
    return {
        "enabled": sec.getboolean("enabled", False),
        "callsign": callsign,
        "passcode": sec.get("passcode", ""),
        "server": sec.get("server", "noam.aprs2.net"),
        "port": int(sec.get("port", 14580)),
        "timeout": float(sec.get("timeout", 10)),
    }


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
    if "baud" in rig:
        result["baud"] = int(rig.get("baud"))
    result["port"] = int(rig.get("port", RIGCTLD_PORT))
    return result
