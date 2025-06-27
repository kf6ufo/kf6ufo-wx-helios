#!/usr/bin/env python3
import psutil
import time
import config
import argparse
import sys
import logging

import utils

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
):
    """Create the APRS information field from telemetry values.

    Parameters
    ----------
    lat, lon : float
        Position in decimal degrees.
    symbol_table : str
        Symbol table identifier.
    symbol : str
        APRS map symbol.
    version : str
        Beacon software version string.
    cpu_temp : float
        CPU temperature in Celsius.
    cpu_load : float
        CPU utilisation percentage.
    uptime_hours : int
        System uptime in hours.
    mem_percent : float
        Memory usage percentage.
    disk_percent : float
        Disk usage percentage.
    net_rx_mb, net_tx_mb : int
        Network usage counters in megabytes.

    Returns
    -------
    str
        APRS information field string.
    """
    position = utils.decimal_to_aprs(lat, lon, symbol_table, symbol)
    comment = (
        f"cpuT={cpu_temp:.1f} load={cpu_load:.0f} upt={uptime_hours}h "
        f"mem={mem_percent:.0f} disk={disk_percent:.0f} "
        f"rx={net_rx_mb} tx={net_tx_mb} ver={version}"
    )
    return position + comment


# Main logic
def main(argv=None):
    """Entry point for running the telemetry beacon."""
    parser = argparse.ArgumentParser(description="APRS Telemetry Beacon")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (no transmit)')
    args = parser.parse_args(argv)

    utils.setup_logging(level=logging.DEBUG if args.debug else logging.INFO)

    tele_cfg = config.load_hubtelemetry_config()
    if not tele_cfg.get("enabled", True):
        utils.log_info("hub_telemetry disabled in configuration", source=__name__)
        sys.exit(0)

    callsign, latitude, longitude, symbol_table, symbol, path, destination, version = config.load_aprs_config()
    if args.debug:
        utils.log_info("Config Loaded:", source=__name__)
        utils.log_info(
            f"callsign={callsign}, lat={latitude}, lon={longitude}, symbol_table={symbol_table}, symbol={symbol}, path={path}, dest={destination}, version={version}"
        , source=__name__)

    telemetry = get_laptop_telemetry()
    if args.debug:
        utils.log_info("Telemetry Collected:", source=__name__)
        utils.log_info(
            f"cpuT={telemetry[0]:.1f}, load={telemetry[1]:.0f}, uptime={telemetry[2]}h, mem={telemetry[3]:.0f}%, disk={telemetry[4]:.0f}%, rx={telemetry[5]}MB, tx={telemetry[6]}MB"
        , source=__name__)

    info = build_aprs_info(latitude, longitude, symbol_table, symbol, version, *telemetry)
    if args.debug:
        utils.log_info("APRS Info Field:", source=__name__)
        utils.log_info(info, source=__name__)

    ax25_frame = utils.build_ax25_frame(destination, callsign, path, info)
    if args.debug:
        utils.log_info("AX25 Frame Built:", source=__name__)
        utils.log_info(ax25_frame.hex(), source=__name__)

    if not args.debug:
        utils.send_via_kiss(ax25_frame)


if __name__ == "__main__":
    main()

