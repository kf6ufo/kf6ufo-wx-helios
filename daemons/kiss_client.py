#!/usr/bin/env python3
"""Background KISS client daemon."""
import socket
import threading
import queue
import time
from pathlib import Path
from utils import log_info, log_exception

import config

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

cfg = config.load_kiss_client_config()
ENABLED = cfg.get("enabled", False)

FRAME_QUEUE = queue.Queue()
_stop = threading.Event()
_socket = None


def _escape(ax25_frame: bytes) -> bytes:
    escaped = bytearray()
    for b in ax25_frame:
        if b == 0xC0:
            escaped += b"\xDB\xDC"
        elif b == 0xDB:
            escaped += b"\xDB\xDD"
        else:
            escaped.append(b)
    return b"\xC0\x00" + bytes(escaped) + b"\xC0"


def _run():
    """Open a single KISS TCP connection and send queued frames."""
    global _socket
    try:
        _socket = socket.create_connection(("127.0.0.1", 8001))
        _socket.settimeout(0.2)
    except Exception:
        log_exception("kiss_client failed to connect", source=LOG_SOURCE)
        return

    try:
        while not _stop.is_set():
            try:
                frame = FRAME_QUEUE.get(timeout=0.2)
            except queue.Empty:
                continue

            if frame is None:
                _stop.set()
                break

            try:
                _socket.send(_escape(frame))
            except Exception:
                log_exception("Failed to send KISS frame", source=LOG_SOURCE)
                break
    finally:
        if _socket:
            try:
                _socket.close()
            except Exception:
                pass
            _socket = None


class _Server:
    def shutdown(self):
        _stop.set()
        FRAME_QUEUE.put(None)


def start():
    """Start the KISS client thread."""
    if not ENABLED:
        log_info("kiss_client disabled in configuration", source=LOG_SOURCE)
        return None, None

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log_info("kiss_client thread started", source=LOG_SOURCE)
    return _Server(), thread
