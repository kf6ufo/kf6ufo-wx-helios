import argparse
import logging
import signal
import subprocess
import sys
import time
from pathlib import Path
import threading
import shutil
import importlib.util
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
    wxnow = runtime_dir / "wxnow.txt"
    direwolf_bin = PROJECT_ROOT / "external" / "direwolf" / "build" / "src" / "direwolf"
    cmd = [str(direwolf_bin), "-c", str(conf), "-l", "direwolf.log", "-w", str(wxnow)]
    logging.info("Starting Direwolf: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def start_rigctld(rig_id: int, usb_num: int):
    rigctld_bin = PROJECT_ROOT / "bin" / "rigctld"
    cmd = [
        str(rigctld_bin),
        "-m",
        str(rig_id),
        "-r",
        f"/dev/ttyUSB{usb_num}",
        "-t",
        "4531",
    ]
    logging.info("Starting rigctld: %s", " ".join(cmd))
    return subprocess.Popen(cmd)


def start_ecowitt_listener():
    cfg = config.load_ecowitt_config()
    if not cfg.get("enabled", True):
        logging.info("Ecowitt listener disabled in configuration")
        return None, None

    spec = importlib.util.spec_from_file_location(
        "ecowitt_listener", PROJECT_ROOT / "ecowitt-listener.py"
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    server = module.HTTPServer(("", module.PORT), module.Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    logging.info("Ecowitt listener running on port %s", module.PORT)
    return server, thread


def run_hubtelemetry():
    cfg = config.load_hubtelemetry_config()
    if not cfg.get("enabled", True):
        logging.info("hubTelemetry disabled in configuration")
        return
    logging.info("Running hubTelemetry.py")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "hubTelemetry.py")])


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
        rigctld_proc = start_rigctld(args.rig_id, args.usb_num)
    else:
        logging.info("rigctld disabled in configuration")
    eco_server, eco_thread = start_ecowitt_listener()

    running = True

    def shutdown(signum, frame):
        nonlocal running
        running = False

    signal.signal(signal.SIGINT, shutdown)
    signal.signal(signal.SIGTERM, shutdown)

    try:
        while running:
            start_time = time.time()
            run_hubtelemetry()
            elapsed = time.time() - start_time
            sleep_left = args.telemetry_interval - elapsed
            while running and sleep_left > 0:
                time.sleep(min(1, sleep_left))
                sleep_left -= 1
    finally:
        logging.info("Shutting down")
        if eco_server is not None:
            eco_server.shutdown()
            eco_thread.join()
        for proc in (direwolf_proc, rigctld_proc):
            if proc:
                proc.terminate()
        for proc in (direwolf_proc, rigctld_proc):
            if proc:
                proc.wait()


if __name__ == "__main__":
    main()
