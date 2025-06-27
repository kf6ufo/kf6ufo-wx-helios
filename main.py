import argparse
import signal
import subprocess
import sys
import time
import os
from pathlib import Path
import threading
import shutil
import importlib
import config
from croniter import croniter
from utils import log_info, log_error, log_exception, setup_logging

LOG_SOURCE = (
    f"{__package__}.{Path(__file__).stem}" if __package__ else Path(__file__).stem
)

PROJECT_ROOT = Path(__file__).resolve().parent


def start_direwolf():
    cfg = config.load_direwolf_config()
    if not cfg.get("enabled", True):
        log_info("Direwolf disabled in configuration", source=LOG_SOURCE)
        return None
    conf = PROJECT_ROOT / "direwolf.conf"
    if not conf.exists():
        shutil.copy(PROJECT_ROOT / "direwolf.conf.template", conf)
    runtime_dir = PROJECT_ROOT / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    direwolf_bin = PROJECT_ROOT / "external" / "direwolf" / "build" / "src" / "direwolf"
    if not direwolf_bin.exists():
        log_error(
            "Direwolf binary not found at %s. Please run build_external.sh first",
            direwolf_bin,
            source=LOG_SOURCE,
        )
        return None
    log_file = PROJECT_ROOT / "direwolf.log"
    cmd = [str(direwolf_bin), "-dttt", "-c", str(conf), "-L", str(log_file)]
    log_info("Starting Direwolf: %s", " ".join(cmd), source=LOG_SOURCE)
    return subprocess.Popen(cmd)


def start_rigctld(rig_id: int, usb_num: int, port: int):
    rigctld_bin = (
        PROJECT_ROOT / "external" / "hamlib" / "build" / "tests" / "rigctld"
    )
    cmd = [
        str(rigctld_bin),
        "-m",
        str(rig_id),
        "-r",
        f"/dev/ttyUSB{usb_num}",
        "-t",
        str(port),
    ]
    log_info("Starting rigctld: %s", " ".join(cmd), source=LOG_SOURCE)
    return subprocess.Popen(cmd)


def start_daemon_modules():
    """Start daemon modules listed in the configuration."""
    daemons = []
    for name in config.load_daemon_modules():
        try:
            log_info("Starting daemon %s", name, source=LOG_SOURCE)
            module = importlib.import_module(name)
            if hasattr(module, "start"):
                server, thread = module.start()
                if server:
                    daemons.append((server, thread))
        except Exception as exc:
            log_exception("Failed to start daemon %s: %s", name, exc, source=LOG_SOURCE)
    return daemons


def run_telemetry_module(name: str):
    """Execute a single telemetry module."""
    try:
        log_info("Running telemetry %s", name, source=LOG_SOURCE)
        env = os.environ.copy()
        subprocess.run([sys.executable, "-m", name], env=env)
    except Exception as exc:
        log_exception("Telemetry module %s failed: %s", name, exc, source=LOG_SOURCE)




def main():
    parser = argparse.ArgumentParser(description="wx-helios combined launcher")
    parser.add_argument("--rig-id", type=int, help="rig model ID")
    parser.add_argument("--usb-num", type=int, help="/dev/ttyUSB device number")
    parser.add_argument(
        "--telemetry-interval",
        type=int,
        default=3600,
        help="seconds between telemetry beacons",
    )
    args = parser.parse_args()

    rig_cfg = config.load_rig_config()
    if args.rig_id is None:
        args.rig_id = rig_cfg.get("rig_id")
    if args.usb_num is None:
        args.usb_num = rig_cfg.get("usb_num")
    if args.rig_id is None or args.usb_num is None:
        parser.error("rig_id and usb_num must be provided via command line or configuration")

    setup_logging()

    direwolf_proc = start_direwolf()
    rigctld_proc = None
    if rig_cfg.get("enabled", True):
        rigctld_proc = start_rigctld(
            args.rig_id,
            args.usb_num,
            rig_cfg.get("port", config.RIGCTLD_PORT),
        )
    else:
        log_info("rigctld disabled in configuration", source=LOG_SOURCE)

    daemon_instances = start_daemon_modules()

    telemetry_modules = config.load_telemetry_modules()
    telemetry_schedules = config.load_telemetry_schedules()
    cron_map = {}
    next_times = {}
    now = time.time()
    for name in telemetry_modules:
        expr = telemetry_schedules.get(name)
        if expr:
            itr = croniter(expr, now)
            cron_map[name] = itr
            next_times[name] = itr.get_next(float)
        else:
            cron_map[name] = None
            next_times[name] = now + args.telemetry_interval

    running = True

    def shutdown(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while running:
            now = time.time()
            for name in telemetry_modules:
                if now >= next_times[name]:
                    run_telemetry_module(name)
                    if cron_map[name]:
                        next_times[name] = cron_map[name].get_next(float)
                    else:
                        next_times[name] = now + args.telemetry_interval

            next_event = min(next_times.values())
            sleep_left = next_event - time.time()
            while running and sleep_left > 0:
                time.sleep(min(1, sleep_left))
                sleep_left -= 1
    finally:
        log_info("Shutting down", source=LOG_SOURCE)
        for server, thread in daemon_instances:
            server.shutdown()
            thread.join()
        for proc in (direwolf_proc, rigctld_proc):
            if proc:
                proc.terminate()
        for proc in (direwolf_proc, rigctld_proc):
            if proc:
                proc.wait()


if __name__ == "__main__":
    main()
