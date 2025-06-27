#!/usr/bin/env python3
"""Background KISS client daemon."""
import socket
import threading
import queue
import time
import os
from multiprocessing.managers import SyncManager
from pathlib import Path
from utils import log_info, log_exception

import config

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

cfg = config.load_kiss_client_config()
ENABLED = cfg.get("enabled", False)
HOST = cfg.get("host", "127.0.0.1")
PORT = cfg.get("port", 8001)

_manager = None
FRAME_QUEUE = None
_stop = threading.Event()
_socket = None


class _QueueManager(SyncManager):
    pass


def _get_frame_queue():
    return FRAME_QUEUE


_QueueManager.register("get_frame_queue", callable=_get_frame_queue)


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
        _socket = socket.create_connection((HOST, PORT))
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
        if FRAME_QUEUE:
            FRAME_QUEUE.put(None)
        if _manager:
            try:
                _manager.shutdown()
            except Exception:
                pass


def start():
    """Start the KISS client thread."""
    if not ENABLED:
        log_info("kiss_client disabled in configuration", source=LOG_SOURCE)
        return None, None

    global _manager, FRAME_QUEUE
    authkey = os.urandom(16)
    _manager = _QueueManager(address=("127.0.0.1", 0), authkey=authkey)
    _manager.start()
    FRAME_QUEUE = _manager.Queue()

    host, port = _manager.address
    os.environ["KISS_MANAGER_HOST"] = host
    os.environ["KISS_MANAGER_PORT"] = str(port)
    os.environ["KISS_MANAGER_AUTHKEY"] = authkey.hex()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log_info("kiss_client thread started", source=LOG_SOURCE)
    return _Server(), thread
