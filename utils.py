"""Shared utility functions used across wx-helios components."""
import socket
import logging
import time
from datetime import datetime, timezone
from pathlib import Path


def setup_logging(level=logging.INFO, use_utc=False):
    """Configure global logging settings.

    Parameters
    ----------
    level : int, optional
        Logging level passed to ``basicConfig``. Defaults to ``logging.INFO``.
    use_utc : bool, optional
        If ``True`` timestamps use UTC. Defaults to ``False``.
    """

    if use_utc:
        logging.Formatter.converter = time.gmtime
    logging.basicConfig(
        level=level,
        format="[%(asctime)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def log_info(message, *args, source=None, **kwargs):
    """Log an informational message.

    Parameters
    ----------
    message : str
        The log message.
    source : str, optional
        Name of the logger to use. If omitted, the root logger is used.
    """

    logger = logging.getLogger(source) if source else logging.getLogger()
    logger.info(message, *args, **kwargs)


def log_error(message, *args, source=None, **kwargs):
    """Log an error message."""

    logger = logging.getLogger(source) if source else logging.getLogger()
    logger.error(message, *args, **kwargs)


def log_exception(message, *args, source=None, **kwargs):
    """Log an exception with traceback."""

    logger = logging.getLogger(source) if source else logging.getLogger()
    logger.exception(message, *args, **kwargs)


# ---------------------------------------------------------------------------
# AX.25/APRS helper functions
# ---------------------------------------------------------------------------

def parse_callsign(full_call: str):
    """Split a callsign of the form ``CALL-SSID``.

    Parameters
    ----------
    full_call : str
        Callsign optionally followed by ``-SSID``.

    Returns
    -------
    tuple[str, int]
        Two-item tuple of the padded callsign and SSID number.
    """

    if "-" in full_call:
        base, ssid = full_call.split("-")
        ssid = int(ssid)
    else:
        base, ssid = full_call, 0
    return base.ljust(6), ssid


def encode_callsign(callsign: str, ssid: int) -> bytearray:
    """Encode a callsign and SSID using AX.25 formatting."""

    encoded = bytearray([(ord(c) << 1) for c in callsign])
    encoded.append(((ssid & 0x0F) << 1) | 0x60)
    return encoded


def build_ax25_frame(destination: str, source: str, path: list[str], info: str) -> bytearray:
    """Construct a UI frame according to the AX.25 protocol."""

    frame = bytearray()
    dest_call, dest_ssid = parse_callsign(destination)
    src_call, src_ssid = parse_callsign(source)
    frame += encode_callsign(dest_call, dest_ssid)
    frame += encode_callsign(src_call, src_ssid)
    for hop in path:
        path_call, path_ssid = parse_callsign(hop)
        frame += encode_callsign(path_call, path_ssid)
    frame[-1] |= 0x01  # End-of-address flag
    frame += b"\x03"  # Control field (UI)
    frame += b"\xF0"  # PID (no layer 3)
    frame += info.encode("ascii")
    return frame


def decimal_to_aprs(lat: float, lon: float, symbol_table: str, symbol: str) -> str:
    """Convert decimal degrees to an APRS position string."""

    ns = "N" if lat >= 0 else "S"
    ew = "E" if lon >= 0 else "W"
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60
    lon_deg = int(abs(lon))
    lon_min = (abs(lon) - lon_deg) * 60

    lat_str = f"{lat_deg:02d}{lat_min:05.2f}{ns}"
    lon_str = f"{lon_deg:03d}{lon_min:05.2f}{ew}"

    return f"!{lat_str}{symbol_table}{lon_str}{symbol}"



def send_via_kiss(ax25_frame):
    """Send a frame via a KISS TCP connection on localhost.

    If the ``kiss_client`` daemon is active, the frame is queued for that
    persistent connection instead of opening a new socket each time.

    Parameters
    ----------
    ax25_frame : bytes or bytearray
        Raw AX.25 frame.

    Returns
    -------
    None
        This function sends data over the network and does not return anything.
    """
    try:
        from daemons import kiss_client
        if getattr(kiss_client, "ENABLED", False) and hasattr(
            kiss_client, "FRAME_QUEUE"
        ):
            kiss_client.FRAME_QUEUE.put(ax25_frame)
            return
    except Exception:
        pass

    escaped = bytearray()
    for b in ax25_frame:
        if b == 0xC0:
            escaped += b"\xDB\xDC"
        elif b == 0xDB:
            escaped += b"\xDB\xDD"
        else:
            escaped.append(b)

    kiss_frame = b"\xC0\x00" + bytes(escaped) + b"\xC0"
    from config import load_kiss_client_config
    cfg = load_kiss_client_config()
    host = cfg.get("host", "127.0.0.1")
    port = cfg.get("port", 8001)
    with socket.create_connection((host, port)) as s:
        s.send(kiss_frame)


