#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import urlparse, parse_qsl
from datetime import datetime, timedelta, timezone
from collections import deque
from pathlib import Path
import logging
import time
import sys
import threading
import config

cfg = config.load_ecowitt_config()
ENABLED = cfg.get("enabled", True)
PORT = cfg.get("port", 8080)
PATH = cfg.get("path", "/data/report")
RAIN_CACHE = deque(maxlen=24)      # store tuples (timestamp, hourly_inch)

try:
    _callsign, _lat_dd, _lon_dd, *_ = config.load_aprs_config()
except Exception:
    _lat_dd = 0.0
    _lon_dd = 0.0

def _format_lat_lon(lat, lon):
    ns = 'N' if lat >= 0 else 'S'
    ew = 'E' if lon >= 0 else 'W'
    lat_deg = int(abs(lat))
    lat_min = (abs(lat) - lat_deg) * 60
    lon_deg = int(abs(lon))
    lon_min = (abs(lon) - lon_deg) * 60
    lat_str = f"{lat_deg:02d}{lat_min:05.2f}{ns}"
    lon_str = f"{lon_deg:03d}{lon_min:05.2f}{ew}"
    return lat_str, lon_str

LAT, LON = _format_lat_lon(_lat_dd, _lon_dd)
POS_BLOCK = f"{LAT}/{LON}_"
# directories
PROJECT_ROOT = Path(__file__).resolve().parent.parent
RUNTIME_DIR = PROJECT_ROOT / "runtime"
RUNTIME_DIR.mkdir(exist_ok=True)
WXNOW = RUNTIME_DIR / "wxnow.txt"

# configure logging to use UTC timestamps
logging.Formatter.converter = time.gmtime
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s UTC] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger(__name__)

def write_wxnow(frame):
    now = datetime.now(timezone.utc).strftime("%b %d %Y %H:%M\n")
    with open(WXNOW, "w") as f:
        f.write(now)
        f.write(frame + "\n")


def update_rain_24h(post):
    """Call once per upload; returns rain last 24 h ×100 for pPPP."""
    # 1) remember this hour’s total
    hour = datetime.strptime(post["dateutc"], "%Y-%m-%d %H:%M:%S").replace(minute=0, second=0)
    hourly = float(post["hourlyrainin"])
    # if last cached hour matches, overwrite; else append
    if RAIN_CACHE and RAIN_CACHE[-1][0] == hour:
        RAIN_CACHE[-1] = (hour, hourly)
    else:
        RAIN_CACHE.append((hour, hourly))

    # 2) toss anything older than 24 h
    cutoff = hour - timedelta(hours=24)
    while RAIN_CACHE and RAIN_CACHE[0][0] < cutoff:
        RAIN_CACHE.popleft()

    # 3) sum and scale
    return int(round(sum(r for _, r in RAIN_CACHE) * 100))

# --- helper ----------------------------------------------------------
def clamp(val, lo, hi):
    """Return val limited to the closed interval [lo, hi]."""
    return max(lo, min(hi, val))

# --- main converter --------------------------------------------------
def ecowitt_to_aprs(p):
    # wind
    wd = clamp(int(float(p["winddir"])), 0, 360)
    ws = clamp(int(float(p["windspeedmph"])), 0, 99)
    wg = clamp(int(float(p["windgustmph"])), 0, 999)

    # temperature
    tf = clamp(int(float(p["tempf"])), -99, 199)
    t_field = f"t{tf:03d}" if tf >= 0 else f"t-{abs(tf):02d}"

    # rainfall
    rain1h  = float(p.get("hourlyrainin", 0))
    rainmid = float(p.get("eventrainin", 0))           # since local midnight
    rRRR = clamp(int(round(rain1h  * 100)), 0, 999)
    PQQQ = clamp(int(round(rainmid * 100)), 0, 999)
    pPPP = clamp(update_rain_24h(p),        0, 999)

    # humidity
    rh_raw = int(float(p["humidity"]))
    rh = 0 if rh_raw <= 0 or rh_raw > 100 else rh_raw

    # pressure (absolute fallback)
    press_in = float(p.get("baromrelin", p.get("baromabsin", 0)))
    bp = clamp(int(round(press_in * 33.8639 * 10)), 0, 19999)

    # timestamp + assemble
    ts = datetime.now(timezone.utc).strftime("%d%H%M")
    return (f"@{ts}z{POS_BLOCK}"
            f"{wd:03d}/{ws:02d}g{wg:03d}"
            f"{t_field}"
            f"r{rRRR:03d}p{pPPP:03d}P{PQQQ:03d}"
            f"h{rh:02d}b{bp:05d}")


def log_params(client, params):
    logger.info("Ecowitt upload from %s", client)
    for k in sorted(params):
        logger.info("  %s: %s", k, params[k])
    frame = ecowitt_to_aprs(params)
    logger.info(frame)
    write_wxnow(frame)


class Handler(BaseHTTPRequestHandler):
    def setup(self):
        super().setup()
        logger.info("Connection from %s:%s", self.client_address[0], self.client_address[1])

    def _okay(self):
        self.send_response(200)
        self.end_headers()
        self.wfile.write(b"OK\n")

    def do_GET(self):
        if not self.path.startswith(PATH):
            self.send_error(404, "Wrong path")
            return
        params = dict(parse_qsl(urlparse(self.path).query))
        log_params(self.client_address[0], params)
        self._okay()

    def do_POST(self):
        if not self.path.startswith(PATH):
            self.send_error(404, "Wrong path")
            return
        # read the URL-encoded body
        length = int(self.headers.get('Content-Length', 0))
        body   = self.rfile.read(length).decode(errors="replace")
        params = dict(parse_qsl(body))
        log_params(self.client_address[0], params)
        self._okay()

    def log_message(self, *_):  # silence default logging
        pass

def start():
    """Start the HTTP listener in a background thread.

    Returns
    -------
    tuple
        ``(server, thread)`` if enabled, otherwise ``(None, None)``.
    """
    if not ENABLED:
        logger.info("Ecowitt listener disabled in configuration")
        return None, None

    server = HTTPServer(("", PORT), Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logger.info("Listening on 0.0.0.0:%s%s", PORT, PATH)
    return server, thread


if __name__ == "__main__":
    srv, th = start()
    if srv and th:
        try:
            th.join()
        except KeyboardInterrupt:
            srv.shutdown()
            th.join()
