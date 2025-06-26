"""Shared utility functions used across wx-helios components."""
import socket


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

