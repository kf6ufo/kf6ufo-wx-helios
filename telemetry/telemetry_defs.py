#!/usr/bin/env python3
"""Transmit APRS telemetry definition messages."""
import argparse
import logging
from pathlib import Path

import config
import utils

LOG_SOURCE = f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem


def _build_def_packets(names, units, bits):
    names = (list(names) + [""] * 5)[:5]
    units = (list(units) + [""] * 5)[:5]
    bits = (list(bits) + [""] * 8)[:8]

    # Definition packets should be sent as APRS messages. Prefix each
    # payload with a colon so the first character is the ":" data type
    # indicator recognized by digipeaters and TNC software.
    parm = ":PARM." + ",".join(names)
    unit = ":UNIT." + ",".join(units + bits)
    eqns = ":EQNS." + ",".join(["0", "1", "0"] * 5)
    bits_line = ":BITS." + ",".join(bits)
    return [parm, unit, eqns, bits_line]


def hub_definitions():
    names = ["cpuT", "cpuLoad", "uptime", "rxMB", "txMB"]
    units = ["C", "%", "h", "MB", "MB"]
    bits = ["diskLow", "memLow"]
    return _build_def_packets(names, units, bits)


def direwolf_definitions():
    names = ["busy", "rcvq", "sendq"]
    units = ["%", "", ""]
    bits = []
    return _build_def_packets(names, units, bits)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Telemetry definition beacon")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args(argv)

    utils.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)

    frames = []
    if config.load_hubtelemetry_config().get("enabled", True):
        defs = hub_definitions()
        callsign, lat, lon, table, sym, path, dest, ver = config.load_aprs_config("HUBTELEMETRY")
        for info in defs:
            frame = utils.build_ax25_frame(dest, callsign, path, info)
            frames.append(frame)

    if config.load_direwolf_config().get("enabled", True):
        defs = direwolf_definitions()
        callsign, lat, lon, table, sym, path, dest, ver = config.load_aprs_config("DIREWOLF_TELEMETRY")
        for info in defs:
            frame = utils.build_ax25_frame(dest, callsign, path, info)
            frames.append(frame)

    for frame in frames:
        if args.debug:
            utils.log_info(frame.hex(), source=LOG_SOURCE)
        else:
            utils.send_via_kiss(frame)


if __name__ == "__main__":
    main()
