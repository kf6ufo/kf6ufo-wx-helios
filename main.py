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

PROJECT_ROOT = Path(__file__).resolve().parent


def start_direwolf():
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
    cmd = [
        "rigctld",
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
    logging.info("Running hubTelemetry.py")
    subprocess.run([sys.executable, str(PROJECT_ROOT / "hubTelemetry.py")])


def main():
    parser = argparse.ArgumentParser(description="wx-helios combined launcher")
    parser.add_argument("rig_id", type=int, help="rig model ID")
    parser.add_argument("usb_num", type=int, help="/dev/ttyUSB device number")
    parser.add_argument(
        "--telemetry-interval",
        type=int,
        default=3600,
        help="seconds between telemetry beacons",
    )
    args = parser.parse_args()

    logging.basicConfig(
        level=logging.INFO,
        format="[%(asctime)s] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    direwolf_proc = start_direwolf()
    rigctld_proc = start_rigctld(args.rig_id, args.usb_num)
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
        eco_server.shutdown()
        eco_thread.join()
        for proc in (direwolf_proc, rigctld_proc):
            proc.terminate()
        for proc in (direwolf_proc, rigctld_proc):
            proc.wait()


if __name__ == "__main__":
    main()
