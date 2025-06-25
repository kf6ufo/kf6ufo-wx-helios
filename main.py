import argparse
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
import threading
import shutil
import importlib
import config

PROJECT_ROOT = Path(__file__).resolve().parent


def start_direwolf():
    cfg = config.load_direwolf_config()
    if not cfg.get("enabled", True):
        logging.info("Direwolf disabled in configuration")
        return None
    conf = PROJECT_ROOT / "direwolf.conf"
    if not conf.exists():
        shutil.copy(PROJECT_ROOT / "direwolf.conf.template", conf)
    runtime_dir = PROJECT_ROOT / "runtime"
    runtime_dir.mkdir(exist_ok=True)
    direwolf_bin = PROJECT_ROOT / "external" / "direwolf" / "build" / "src" / "direwolf"
    cmd = [str(direwolf_bin), "-c", str(conf), "-l", "direwolf.log"]
    logging.info("Starting Direwolf: %s", " ".join(cmd))
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
    logging.info("Starting rigctld: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def start_daemon_modules():
    """Start daemon modules listed in the configuration."""
    daemons = []
    for name in config.load_daemon_modules():
        try:
            logging.info("Starting daemon %s", name)
            module = importlib.import_module(name)
            if hasattr(module, "start"):
                server, thread = module.start()
                if server:
                    daemons.append((server, thread))
        except Exception as exc:
            logging.exception("Failed to start daemon %s: %s", name, exc)
    return daemons


def run_telemetry_modules():
    """Execute all telemetry modules sequentially."""
    for name in config.load_telemetry_modules():
        try:
            logging.info("Running telemetry %s", name)
            subprocess.run([sys.executable, "-m", name])
        except Exception as exc:
            logging.exception("Telemetry module %s failed: %s", name, exc)




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

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    direwolf_proc = start_direwolf()
    rigctld_proc = None
    if rig_cfg.get("enabled", True):
        rigctld_proc = start_rigctld(
            args.rig_id,
            args.usb_num,
            rig_cfg.get("port", config.RIGCTLD_PORT),
        )
    else:
        logging.info("rigctld disabled in configuration")

    daemon_instances = start_daemon_modules()

    running = True

    def shutdown(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while running:
            start_time = time.time()
            run_telemetry_modules()
            elapsed = time.time() - start_time
            sleep_left = args.telemetry_interval - elapsed
            while running and sleep_left > 0:
                time.sleep(min(1, sleep_left))
                sleep_left -= 1
    finally:
        logging.info("Shutting down")
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
