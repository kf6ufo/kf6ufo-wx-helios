#!/usr/bin/env python3
"""Background KISS client daemon."""
import socket
import threading
import queue
import logging

import config

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
    global _socket
    try:
        _socket = socket.create_connection(("127.0.0.1", 8001))
        while not _stop.is_set():
            frame = FRAME_QUEUE.get()
            if frame is None:
                break
            try:
                _socket.send(_escape(frame))
            except Exception:
                logging.exception("Failed to send KISS frame")
    except Exception:
        logging.exception("kiss_client failed to connect")
    finally:
        if _socket:
            try:
                _socket.close()
            except Exception:
                pass


class _Server:
    def shutdown(self):
        _stop.set()
        FRAME_QUEUE.put(None)


def start():
    """Start the KISS client thread."""
    if not ENABLED:
        logging.info("kiss_client disabled in configuration")
        return None, None

    thread = threading.Thread(target=_run, daemon=True)
    thread.start()
    return _Server(), thread
