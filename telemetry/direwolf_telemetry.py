#!/usr/bin/env python3
import argparse
import sys
import re
from pathlib import Path

import config
from telemetry import hub_telemetry

LOG_PATH = Path(__file__).resolve().parent.parent / "direwolf.log"


def parse_metrics(line):
    """Extract metrics from a Direwolf telemetry line."""
    metrics = {}
    m = re.search(r"rcvq=(\d+)", line)
    if m:
        metrics["rcvq"] = int(m.group(1))
    m = re.search(r"sendq=(\d+)", line)
    if m:
        metrics["sendq"] = int(m.group(1))
    m = re.search(r"busy=([0-9.]+)", line)
    if m:
        metrics["busy"] = float(m.group(1))
    return metrics


def read_metrics(path=LOG_PATH):
    """Return the most recent set of metrics from ``direwolf.log``."""
    try:
        with open(path, "r") as f:
            lines = f.readlines()
    except FileNotFoundError:
        return None
    for line in reversed(lines):
        if "busy=" in line and "sendq=" in line:
            data = parse_metrics(line)
            if data:
                return data
    return None


def build_aprs_info(lat, lon, table, symbol, version, metrics):
    pos = hub_telemetry.decimal_to_aprs(lat, lon, table, symbol)
    comment = (
        f"dw_busy={metrics.get('busy', 0):.1f} "
        f"dw_rcvq={metrics.get('rcvq', 0)} "
        f"dw_sendq={metrics.get('sendq', 0)} ver={version}"
    )
    return pos + comment


def main(argv=None):
    parser = argparse.ArgumentParser(description="Direwolf Telemetry Beacon")
    parser.add_argument("--debug", action="store_true", help="Enable debug mode")
    args = parser.parse_args(argv)

    cfg = config.load_direwolf_config()
    if not cfg.get("enabled", True):
        if args.debug:
            print("direwolf telemetry disabled in configuration")
        sys.exit(0)

    metrics = read_metrics()
    if not metrics:
        if args.debug:
            print("No telemetry metrics found")
        sys.exit(1)

    callsign, lat, lon, table, symbol, path, dest, ver = config.load_aprs_config()
    info = build_aprs_info(lat, lon, table, symbol, ver, metrics)
    frame = hub_telemetry.build_ax25_frame(dest, callsign, path, info)

    if args.debug:
        print(info)
        print(frame.hex())
    else:
        hub_telemetry.send_via_kiss(frame)


if __name__ == "__main__":
    main()
