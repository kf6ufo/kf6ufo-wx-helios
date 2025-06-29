#!/usr/bin/env python3
import argparse
import sys
import re
import logging
from pathlib import Path

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

import config
import utils

LOG_PATH = Path(__file__).resolve().parent.parent / "log"


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
    """Return the most recent set of metrics from ``direwolf.log``.

    ``path`` may point directly to a log file or a directory containing
    rotated log files.  When a directory is provided, the newest ``*.log``
    file inside the directory is used.
    """
    p = Path(path)
    if p.is_dir():
        log_files = sorted(
            [f for f in p.glob("*.log") if f.is_file()],
            key=lambda f: f.stat().st_mtime,
            reverse=True,
        )
        if not log_files:
            return None
        p = log_files[0]

    try:
        with p.open("r") as f:
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
    pos = utils.decimal_to_aprs(lat, lon, table, symbol)
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

    utils.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)

    cfg = config.load_direwolf_config()
    if not cfg.get("enabled", True):
        utils.log_info("direwolf telemetry disabled in configuration", source=LOG_SOURCE)
        sys.exit(0)

    metrics = read_metrics()
    if not metrics:
        utils.log_info(
            "No telemetry metrics found, sending zeros", source=LOG_SOURCE
        )
        metrics = {}

    callsign, lat, lon, table, symbol, path, dest, ver = config.load_aprs_config("DIREWOLF_TELEMETRY")
    info = build_aprs_info(lat, lon, table, symbol, ver, metrics)
    frame = utils.build_ax25_frame(dest, callsign, path, info)

    if args.debug:
        utils.log_info(info, source=LOG_SOURCE)
        utils.log_info(frame.hex(), source=LOG_SOURCE)
    else:
        utils.send_via_kiss(frame)


if __name__ == "__main__":
    main()
