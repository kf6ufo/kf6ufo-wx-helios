# KF6UFO wx‑helios

A simple APRS telemetry beacon intended for Raspberry Pi and other small computers. This repository forms the core of the **wx‑helios** project—a solar‑powered APRS weather and telemetry suite for amateur radio.

## Hardware platforms

The same Python code can be deployed on three target platforms:

1. **Radio/Computer** – a generic setup for testing or casual use on any amateur station.
2. **Production** – a quality build using the DigiRig interface, a Yaesu FT‑65R handheld, and a Raspberry Pi 4.
3. **Cheapest** – the lowest‑cost option with a USB audio dongle, a simple PTT circuit, a Baofeng radio, and (if possible) a Raspberry Pi 3.

## Repository modules

The project will expand to include several related components:

- `wx-helios-direwolf` and `wx-helios-direwolf telemetry`
- `wx-helios repeater` and `wx-helios repeater telemetry`
- `weather station` support (currently HP2551 Wi‑Fi Weather) with APRS reports and telemetry
- `wx-helios controller` and `wx-helios controller telemetry`
- `wx-helios transceiver` and `wx-helios transceiver telemetry`
- `wx-helios solar-power controller` and `wx-helios solar-power controller telemetry`
- `wx-helios solar-panels` and `wx-helios solar-panels telemetry`

## Supported weather stations

This project receives weather data via the **Ecowitt** protocol. The integration
has only been tested with an **Ecowitt HP2551 Wi-Fi** station, but any weather
station that speaks the same protocol should also work.

## Features

- APRS position and telemetry embedded in a human-readable comment
- Configuration via an INI file
- Works with the Direwolf KISS interface
- Portable across hardware platforms
- Reliable symbol handling with a simple beacon loop for telemetry extraction
- Weather-station integration via the Ecowitt protocol
- Runtime directory with `wxnow.txt` holding the latest APRS frame

## Requirements

- Debian / Ubuntu / Raspberry Pi OS
- Python 3.x
- Python dependencies listed in `requirements.txt` (install with `pip install -r requirements.txt`)

## Building external components

This repository includes the
[wx-helios-direwolf](https://github.com/kf6ufo/wx-helios-direwolf) and
[wx-helios-hamlib](https://github.com/kf6ufo/wx-helios-hamlib) submodules used
to provide the Direwolf TNC and the `rigctld` daemon. Simply run the helper
script to fetch the latest sources, install the build requirements and compile
both projects. Hamlib is built first so Direwolf can detect the libraries. The
script installs GNU autotools if needed, runs Hamlib's `./bootstrap` to create
the `configure` script, invokes the traditional `configure` build and uses
CMake for Direwolf:

```bash
./build_external.sh
```

After building, `main.py` will automatically launch Direwolf and `rigctld`
whenever they are enabled in ``wx-helios.conf``. The separate helper scripts
previously used to start these services have been removed.


## Configuration

Copy the template and edit the values for your station:

```bash
cp wx-helios.conf.template wx-helios.conf
```

Telemetry sequence counters are no longer used, so the previous
`[TELEMETRY]/sequence_file` option has been removed.

The file contains APRS beacon details, Ecowitt listener settings and radio
parameters. Each service can be disabled with an ``enabled`` option:
``[ECOWITT]/enabled`` for the listener, ``[HUBTELEMETRY]/enabled`` for the
telemetry beacon, ``[DIREWOLF]/enabled`` for the TNC and ``[RIG]/enabled`` for
``rigctld``. The ``[RIG]`` section also provides ``rig_id`` and ``usb_num`` for
``rigctld``. Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Runtime directory

Scripts create writable files under `runtime/` in the project root. For example,
`ecowitt-listener.py` writes the latest APRS frame to `runtime/wxnow.txt` each
time it logs data.

## Combined launcher

`main.py` starts all services at once. It reads the rig model and USB number
from ``wx-helios.conf`` by default. Command-line options ``--rig-id`` and
``--usb-num`` override the configuration if needed. The telemetry beacon runs
every hour until the program is stopped.

The provided ``run.sh`` script launches ``main.py`` with a Python interpreter
from a local virtual environment if one exists, falling back to ``python3``
otherwise. Simply execute:

```bash
./run.sh
```

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
