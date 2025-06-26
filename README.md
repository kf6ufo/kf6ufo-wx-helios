# KF6UFO wx‑helios

**wx‑helios** is a solar‑powered APRS weather and telemetry suite for amateur radio.  It employs a
simple **Direwolf**-based APRS telemetry beacon intended for small computers and Raspberry Pi. 

## Weather stations

This project currently only receives weather data via the **Ecowitt** protocol. The integration
has only been tested with an **Ecowitt HP2551 Wi-Fi** station, but any weather
station that speaks the same protocol should also work.  A daemon architecture supports
other protocols, but currently there is only the **Ecowitt** daemon/listener.

## Requirements

- Debian / Ubuntu / Raspberry Pi OS
- Python 3.x
- Python dependencies listed in `requirements.txt` (install into `.venv` with `pip install -r requirements.txt` or simply run `./run.sh`)

## Hardware platforms

The same Python code can be deployed on three target platforms:

1. **Radio/Computer** – a generic setup for testing or casual use on any amateur station.
2. **Production** – a quality build using the DigiRig interface, a Yaesu FT‑65R handheld, and a Raspberry Pi 4.
3. **Cheapest** – the lowest‑cost option with a USB audio dongle, a simple PTT circuit, a Baofeng radio, and (if possible) a Raspberry Pi 3.

## Building external components

This repository includes the
[wx-helios-direwolf](https://github.com/kf6ufo/wx-helios-direwolf) and
[wx-helios-hamlib](https://github.com/kf6ufo/wx-helios-hamlib) submodules used
to provide the Direwolf TNC and the `rigctld` daemon. Simply run the build
script to fetch the latest sources and compile both projects. Hamlib is built
first so Direwolf can detect the libraries and use the correct ``rigctld``.

```bash
./build_external.sh
```

## Configuration

Copy the templates and edit the values for your station:

```bash
cp wx-helios.conf.template wx-helios.conf
cp direwolf.conf.template direwolf.conf
```

The files contains configuration settings for the ``Direwolf TNC`` and **kf6ufo-wx-helios**.
``Direwolf`` can be used by itself to handle PTT on the radio, or ``rigctld`` is included
for more options in handling PTT.
If ``rigctld`` is enabled, be sure that the ``Direwolf`` port for ``rigctld`` is the same
as is configured for ``rigctld`` in ``wx-helios,conf``

Telemetry modules can be scheduled individually using cron syntax.  

```ini
[TELEMETRY_SCHEDULES]
telemetry.hub_telemetry = 0 * * * *
#other.module = */15 * * * *
```

## Running kf6ufo-wx-helios

The provided ``run.sh`` script ensures the ``.venv`` environment exists,
installs dependencies if necessary, activates the ``.venv`` and then launches ``main.py`` using that interpreter.
`main.py` starts all the services and daemons, then schedules telemetry runs. 
Simply execute:

```bash
./run.sh
```

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
