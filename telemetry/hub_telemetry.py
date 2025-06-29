#!/usr/bin/env python3
import psutil
import time
import config
import argparse
import sys
import logging
from pathlib import Path

import utils

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

# Collect system telemetry
def get_laptop_telemetry():
    """Gather basic system metrics using ``psutil``.

    Returns
    -------
    tuple
        ``(cpu_temp, cpu_load, uptime_hours, mem_percent, disk_percent,
        net_rx_mb, net_tx_mb)``.
    """
    cpu_temp = 0.0
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            cpu_temp = temps['coretemp'][0].current
    except Exception:
        cpu_temp = 0.0

    cpu_load = psutil.cpu_percent(interval=1)
    uptime_sec = int(time.time() - psutil.boot_time())
    uptime_hours = uptime_sec // 3600

    mem = psutil.virtual_memory()
    mem_percent = mem.percent

    disk = psutil.disk_usage('/')
    disk_percent = disk.percent

    net = psutil.net_io_counters()
    net_rx_mb = int(net.bytes_recv / 1024 / 1024)
    net_tx_mb = int(net.bytes_sent / 1024 / 1024)

    return cpu_temp, cpu_load, uptime_hours, mem_percent, disk_percent, net_rx_mb, net_tx_mb


# Build APRS info field with key=value pairs
def build_aprs_info(
    lat,
    lon,
    symbol_table,
    symbol,
    version,
    cpu_temp,
    cpu_load,
    uptime_hours,
    mem_percent,
    disk_percent,
    net_rx_mb,
    net_tx_mb,
    seq=0,
):
    """Create an APRS telemetry packet from system metrics."""

    analog = [
        cpu_temp,
        cpu_load,
        uptime_hours,
        net_rx_mb,
        net_tx_mb,
    ]

    disk_low = disk_percent >= 90
    mem_low = mem_percent >= 90

    comment = f"ver={version}"
    return utils.build_aprs_telemetry(seq, analog=analog, digital=[disk_low, mem_low], comment=comment)


# Main logic
def main(argv=None):
    """Entry point for running the telemetry beacon."""
    parser = argparse.ArgumentParser(description="APRS Telemetry Beacon")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (no transmit)')
    args = parser.parse_args(argv)

    utils.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)

    tele_cfg = config.load_hubtelemetry_config()
    if not tele_cfg.get("enabled", True):
        utils.log_info("hub_telemetry disabled in configuration", source=LOG_SOURCE)
        sys.exit(0)

    callsign, latitude, longitude, symbol_table, symbol, path, destination, version = config.load_aprs_config("HUBTELEMETRY")
    if args.debug:
        utils.log_info("Config Loaded:", source=LOG_SOURCE)
        utils.log_info(
            f"callsign={callsign}, lat={latitude}, lon={longitude}, symbol_table={symbol_table}, symbol={symbol}, path={path}, dest={destination}, version={version}"
        , source=LOG_SOURCE)

    telemetry = get_laptop_telemetry()
    if args.debug:
        utils.log_info("Telemetry Collected:", source=LOG_SOURCE)
        utils.log_info(
            f"cpuT={telemetry[0]:.1f}, load={telemetry[1]:.0f}, uptime={telemetry[2]}h, mem={telemetry[3]:.0f}%, disk={telemetry[4]:.0f}%, rx={telemetry[5]}MB, tx={telemetry[6]}MB"
        , source=LOG_SOURCE)

    info = build_aprs_info(latitude, longitude, symbol_table, symbol, version, *telemetry)
    if args.debug:
        utils.log_info("APRS Info Field:", source=LOG_SOURCE)
        utils.log_info(info, source=LOG_SOURCE)

    ax25_frame = utils.build_ax25_frame(destination, callsign, path, info)
    if args.debug:
        utils.log_info("AX25 Frame Built:", source=LOG_SOURCE)
        utils.log_info(ax25_frame.hex(), source=LOG_SOURCE)

    if not args.debug:
        utils.send_via_kiss(ax25_frame)


if __name__ == "__main__":
    main()

