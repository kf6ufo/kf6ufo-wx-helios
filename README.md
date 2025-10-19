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
- Python dependencies listed in `requirements.txt` are loaded automatically into a python venv by ``run.sh``

## Hardware platforms

The same Python code can be deployed on at least three target platforms:

1. **Radio/Computer** – a generic setup for testing or casual use on any amateur station.
2. **Production** – a quality build using the DigiRig interface, a Yaesu FT‑65R handheld, and a Raspberry Pi 4.
3. **Cheapest** – the lowest‑cost option with a USB audio dongle, a simple PTT circuit, a Baofeng radio, and (if possible) a Raspberry Pi 3.

## Building external components

This repository includes the
[wx-helios-direwolf](https://github.com/kf6ufo/wx-helios-direwolf) and
[wx-helios-hamlib](https://github.com/kf6ufo/wx-helios-hamlib) submodules used
to provide the Direwolf TNC and the `rigctld` daemon. Before building, install
the required development packages so CMake can locate ALSA and other
dependencies:

```bash
sudo apt-get install build-essential cmake libasound2-dev pkg-config
```

Download the repo with submodules into your development base:
```bash
git clone --recurse-submodules https://github.com/kf6ufo/kf6ufo-wx-helios.git
```

Then run the build script to fetch the latest
sources and compile both projects. Hamlib is built first so Direwolf can detect
the libraries and use the correct ``rigctld``.

```bash
cd kf6ufo-wx-helios/
./build_external.sh
```

The script also installs Direwolf into ``external/direwolf/install`` so its
runtime data files are available. If you build Direwolf manually, run
``make install`` or set the ``DIREWOLF_DIR`` environment variable to the install
prefix to avoid warnings about missing ``symbols-new.txt`` and ``tocalls.txt``.

## Configuration

Copy the templates and edit the values for your station:

```bash
cp wx-helios.conf.template wx-helios.conf
cp direwolf.conf.template direwolf.conf
```

The files contains configuration settings for the ``Direwolf TNC`` and **kf6ufo-wx-helios**.
The minimum changes you'll need to make are in ``wx-helios.conf`` to edit your **callsign**,
**latitude** and **longitude**.
To forward packets to APRS-IS set the options in the ``[APRS_IS]`` section with
your passcode and server details. The configuration template defaults the server
to ``noam.aprs2.net`` which is recommended for North American clients. Adjust
the ``server`` option if you are in a different region. When enabling APRS-IS,
also add ``daemons.aprsis_client`` to the module list in the ``[DAEMONS]``
section so the APRS-IS client starts.

``Direwolf`` can be used by itself to handle PTT on the radio, or ``rigctld`` is included
for more options in handling PTT.
If ``rigctld`` is enabled, be sure that the ``Direwolf`` port for ``rigctld`` is the same
as is configured for ``rigctld`` in ``wx-helios,conf``. 

## Running kf6ufo-wx-helios

The provided ``run.sh`` script launches the project and ensures the environment is setup.
Simply execute:

```bash
./run.sh
```

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
