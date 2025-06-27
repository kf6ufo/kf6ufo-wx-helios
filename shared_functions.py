"""Shared utility functions used across wx-helios components."""
import socket
from datetime import datetime, timezone
from pathlib import Path

# Location of the runtime directory and ``wxnow.txt`` file.  These are used
# by ``send_via_wxnow`` when writing the current weather frame.
PROJECT_ROOT = Path(__file__).resolve().parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)
WXNOW = RUNTIME_DIR / "wxnow.txt"


def send_via_kiss(ax25_frame):
    """Send a frame via a KISS TCP connection on localhost.

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
        if (
            getattr(kiss_client, "ENABLED", False)
            and hasattr(kiss_client, "FRAME_QUEUE")
            and getattr(kiss_client, "_socket", None) is not None
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
    with socket.create_connection(("127.0.0.1", 8001)) as s:
        s.send(kiss_frame)


def send_via_wxnow(frame: str) -> None:
    """Write an APRS weather frame to ``wxnow.txt``.

    Parameters
    ----------
    frame : str
        The APRS text frame to record.
    """
    timestamp = datetime.now(timezone.utc).strftime("%b %d %Y %H:%M\n")
    with open(WXNOW, "w") as f:
        f.write(timestamp)
        f.write(frame + "\n")

