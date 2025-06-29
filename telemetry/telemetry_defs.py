#!/usr/bin/env python3
"""Transmit APRS telemetry definition messages."""
import argparse
import logging
from pathlib import Path

import config
import utils

LOG_SOURCE = f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem


def _build_def_packets(names, units, bits, addressee):
    names = (list(names) + [""] * 5)[:5]
    units = (list(units) + [""] * 5)[:5]
    bits = (list(bits) + [""] * 8)[:8]

    addr_field = addressee.ljust(9)[:9]
    prefix = f":{addr_field}:"

    parm = prefix + "PARM." + ",".join(names)
    unit = prefix + "UNIT." + ",".join(units + bits)
    eqns = prefix + "EQNS." + ",".join(["0", "1", "0"] * 5)
    bits_line = prefix + "BITS." + ",".join(bits)
    return [parm, unit, eqns, bits_line]


def hub_definitions(addressee):
    names = ["cpuT", "cpuLoad", "uptime", "rxMB", "txMB"]
    units = ["C", "%", "h", "MB", "MB"]
    bits = ["diskLow", "memLow"]
    return _build_def_packets(names, units, bits, addressee)


def direwolf_definitions(addressee):
    names = ["busy", "rcvq", "sendq"]
    units = ["%", "", ""]
    bits = []
    return _build_def_packets(names, units, bits, addressee)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Telemetry definition beacon")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args(argv)

    utils.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)

    frames = []
    if config.load_hubtelemetry_config().get("enabled", True):
        callsign, lat, lon, table, sym, path, dest, ver = config.load_aprs_config("HUBTELEMETRY")
        defs = hub_definitions(dest)
        for info in defs:
            frame = utils.build_ax25_frame(dest, callsign, path, info)
            frames.append(frame)

    if config.load_direwolf_config().get("enabled", True):
        callsign, lat, lon, table, sym, path, dest, ver = config.load_aprs_config("DIREWOLF_TELEMETRY")
        defs = direwolf_definitions(dest)
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
