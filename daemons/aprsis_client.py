#!/usr/bin/env python3
"""Background APRS-IS client daemon."""

import socket
import threading
import queue
import time
import os
import multiprocessing
from multiprocessing.managers import SyncManager
from pathlib import Path
from utils import log_info, log_exception

import config

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

cfg = config.load_aprsis_config()
ENABLED = cfg.get("enabled", False)
HOST = cfg.get("server")
PORT = cfg.get("port")
CALLSIGN = cfg.get("callsign")
PASSCODE = cfg.get("passcode")
TIMEOUT = cfg.get("timeout", 10)

_manager = None
FRAME_QUEUE = None
_stop = threading.Event()
_socket = None


class _QueueManager(SyncManager):
    pass


def _get_frame_queue():
    return FRAME_QUEUE


_QUEUE_METHODS = (
    "empty",
    "full",
    "get",
    "get_nowait",
    "join",
    "put",
    "put_nowait",
    "qsize",
    "task_done",
)



def _connect_with_retry():
    """Return a connected socket, retrying until stop is signaled."""
    while not _stop.is_set():
        try:
            sock = socket.create_connection((HOST, PORT), timeout=TIMEOUT)
            login = f"user {CALLSIGN} pass {PASSCODE} vers wx-helios 0\r\n".encode()
            sock.sendall(login)
            sock.settimeout(0.2)
            return sock
        except Exception:
            time.sleep(0.2)
    return None


def _run():
    """Open APRS-IS connection and send queued frames."""
    global _socket
    _socket = _connect_with_retry()
    if not _socket:
        log_exception("aprsis_client failed to connect", source=LOG_SOURCE)
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
                _socket.sendall((frame + "\r\n").encode())
            except Exception:
                log_exception("Failed to send APRS-IS frame", source=LOG_SOURCE)
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
    """Start the APRS-IS client thread."""
    if not ENABLED:
        log_info("aprsis_client disabled in configuration", source=LOG_SOURCE)
        return None, None

    global _manager, FRAME_QUEUE
    authkey = os.urandom(16)
    FRAME_QUEUE = multiprocessing.Queue()

    _QueueManager.register(
        "get_frame_queue",
        callable=lambda: FRAME_QUEUE,
        exposed=_QUEUE_METHODS,
    )

    _manager = _QueueManager(address=("127.0.0.1", 0), authkey=authkey)
    _manager.start()

    _stop.clear()

    host, port = _manager.address
    os.environ["APRSIS_MANAGER_HOST"] = host
    os.environ["APRSIS_MANAGER_PORT"] = str(port)
    os.environ["APRSIS_MANAGER_AUTHKEY"] = authkey.hex()

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    log_info("aprsis_client thread started", source=LOG_SOURCE)
    return _Server(), thread
