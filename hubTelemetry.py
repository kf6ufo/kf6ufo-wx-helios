import psutil
import socket
import time
import configparser
import argparse

# Load configuration from file
def load_config():
    config = configparser.ConfigParser()
    config.read("hubTelemetry.conf")
    callsign = config["APRS"]["callsign"]
    latitude = float(config["APRS"]["latitude"])
    longitude = float(config["APRS"]["longitude"])
    symbol_table_raw = config["APRS"]["symbol_table"].strip().lower()
    if symbol_table_raw == "primary":
        symbol_table = '/'
    elif symbol_table_raw == "secondary":
        symbol_table = '\\'
    else:
        symbol_table = '/'
    symbol = config["APRS"]["symbol"]
    path = [x.strip() for x in config["APRS"]["path"].split(",")]
    destination = config["APRS"]["destination"]
    version = config["APRS"].get("version", "v5")
    return callsign, latitude, longitude, symbol_table, symbol, path, destination, version

# Parse callsign with optional SSID
def parse_callsign(full_call):
    if '-' in full_call:
        base, ssid = full_call.split('-')
        ssid = int(ssid)
    else:
        base, ssid = full_call, 0
    return base.ljust(6), ssid

# AX.25 callsign encoding
def encode_callsign(callsign, ssid):
    encoded = bytearray([(ord(c) << 1) for c in callsign])
    encoded.append(((ssid & 0x0F) << 1) | 0x60)
    return encoded

# Build full AX.25 UI frame
def build_ax25_frame(destination, source, path, info):
    frame = bytearray()
    dest_call, dest_ssid = parse_callsign(destination)
    src_call, src_ssid = parse_callsign(source)
    frame += encode_callsign(dest_call, dest_ssid)
    frame += encode_callsign(src_call, src_ssid)
    for hop in path:
        path_call, path_ssid = parse_callsign(hop)
        frame += encode_callsign(path_call, path_ssid)
    frame[-1] |= 0x01  # End-of-address flag
    frame += b'\x03'  # Control field (UI)
    frame += b'\xF0'  # PID (no layer 3)
    frame += info.encode('ascii')
    return frame

# Collect system telemetry
def get_laptop_telemetry():
    cpu_temp = 0.0
    try:
        temps = psutil.sensors_temperatures()
        if 'coretemp' in temps:
            cpu_temp = temps['coretemp'][0].current
    except:
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

# Convert decimal degrees to APRS position format
def decimal_to_aprs(lat, lon, symbol_table, symbol):
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60
    lon_deg = int(abs(lon))
    lon_min = (abs(lon) - lon_deg) * 60

    lat_str = f"{lat_deg:02d}{lat_min:05.2f}{ns}"
    lon_str = f"{lon_deg:03d}{lon_min:05.2f}{ew}"

    return f"!{lat_str}{symbol_table}{lon_str}{symbol}"

# Build APRS info field with key=value pairs
def build_aprs_info(lat, lon, symbol_table, symbol, version, cpu_temp, cpu_load, uptime_hours, mem_percent, disk_percent, net_rx_mb, net_tx_mb):
    position = decimal_to_aprs(lat, lon, symbol_table, symbol)
    comment = (
        f"cpuT={cpu_temp:.1f} load={cpu_load:.0f} upt={uptime_hours}h "
        f"mem={mem_percent:.0f} disk={disk_percent:.0f} "
        f"rx={net_rx_mb} tx={net_tx_mb} ver={version}"
    )
    return position + comment

# Send KISS frame to Direwolf
def send_via_kiss(ax25_frame):
    kiss_frame = b'\xC0\x00' + ax25_frame + b'\xC0'
    with socket.create_connection(("127.0.0.1", 8001)) as s:
        s.send(kiss_frame)

# Main logic
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="APRS Telemetry Beacon")
    parser.add_argument('--debug', action='store_true', help='Enable debug mode (no transmit)')
    args = parser.parse_args()

    callsign, latitude, longitude, symbol_table, symbol, path, destination, version = load_config()
    if args.debug:
        print("Config Loaded:")
        print(f"callsign={callsign}, lat={latitude}, lon={longitude}, symbol_table={symbol_table}, symbol={symbol}, path={path}, dest={destination}, version={version}")

    telemetry = get_laptop_telemetry()
    if args.debug:
        print("Telemetry Collected:")
        print(f"cpuT={telemetry[0]:.1f}, load={telemetry[1]:.0f}, uptime={telemetry[2]}h, mem={telemetry[3]:.0f}%, disk={telemetry[4]:.0f}%, rx={telemetry[5]}MB, tx={telemetry[6]}MB")

    info = build_aprs_info(latitude, longitude, symbol_table, symbol, version, *telemetry)
    if args.debug:
        print("APRS Info Field:")
        print(info)

    ax25_frame = build_ax25_frame(destination, callsign, path, info)
    if args.debug:
        print("AX25 Frame Built:")
        print(ax25_frame.hex())

    if not args.debug:
        send_via_kiss(ax25_frame)

