# KF6UFO wx‑helios

A simple APRS telemetry beacon intended for Raspberry Pi and other small computers. This repository forms the core of the **wx‑helios** project—a solar‑powered APRS weather and telemetry suite for amateur radio.

## Hardware platforms

The same Python code can be deployed on three target platforms:

1. **Radio/Computer** – a generic setup for testing or casual use on any amateur station.
2. **Production** – a quality build using the DigiRig interface, a Yaesu FT‑65R handheld, and a Raspberry Pi 4.
3. **Cheapest** – the lowest‑cost option with a USB audio dongle, a simple PTT circuit, a Baofeng radio, and (if possible) a Raspberry Pi 3.


## Supported weather stations

This project receives weather data via the **Ecowitt** protocol. The integration
has only been tested with an **Ecowitt HP2551 Wi-Fi** station, but any weather
station that speaks the same protocol should also work.


## Requirements

- Debian / Ubuntu / Raspberry Pi OS
- Python 3.x
- Python dependencies listed in `requirements.txt` (install with `pip install -r requirements.txt`)

## Building external components

This repository includes the
[wx-helios-direwolf](https://github.com/kf6ufo/wx-helios-direwolf) and
[wx-helios-hamlib](https://github.com/kf6ufo/wx-helios-hamlib) submodules used
to provide the Direwolf TNC and the `rigctld` daemon. Simply run the helper
script to fetch the latest sources and compile both projects. Hamlib is built
first so Direwolf can detect the libraries. The script installs GNU autotools
if needed and runs Hamlib's `./bootstrap` to create the `configure` script.
The resulting `rigctld` binary is left inside
`external/hamlib/build/tests/` and Direwolf is built with CMake:

```bash
./build_external.sh
```

After building, `main.py` will automatically launch Direwolf and `rigctld`
whenever they are enabled in ``wx-helios.conf``. The separate helper scripts
previously used to start these services have been removed.


## Configuration

Copy the templates and edit the values for your station:

```bash
cp wx-helios.conf.template wx-helios.conf
cp direwolf.conf.template direwolf.conf
```

The file contains APRS beacon details, Ecowitt listener settings and radio
parameters. Services are enabled via ``[DAEMONS]`` and ``[TELEMETRY]`` lists of
module names. Existing sections such as ``[ECOWITT]`` and ``[HUBTELEMETRY]``
provide per-module options. ``[DIREWOLF]/enabled`` controls the TNC and
``[RIG]/enabled`` controls ``rigctld``. The ``[RIG]`` section also provides
``rig_id``, ``usb_num`` and ``port`` for ``rigctld``; the template defaults to
``rig_id = 1`` for the Hamlib dummy radio. The ``port`` option must match the
``PTT RIG`` port in ``direwolf.conf`` and is used by ``main.py`` when launching
``rigctld``.

### Python virtual environment

Create and activate a local environment:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies inside this environment:

```bash
pip install -r requirements.txt
```

The `run.sh` script automatically uses this environment.

## Running kf6ufo-wx-helios

`main.py` starts all services at once. It reads the rig model and USB number
from ``wx-helios.conf`` by default.

The provided ``run.sh`` script launches ``main.py`` with a Python interpreter
from a local virtual environment if one exists, falling back to ``python3``
otherwise. Simply execute:

```bash
./run.sh
```

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
