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

## Building wx-helios-direwolf

This repository includes the [wx-helios-direwolf](https://github.com/kf6ufo/wx-helios-direwolf) subproject used to provide the Direwolf TNC. Build it before running the telemetry beacon using the helper script:

```bash
./build_direwolf.sh
```

## Running wx-helios-direwolf

Start the Direwolf TNC with the helper script:

```bash
./run_direwolf.sh
```

This uses `direwolf.conf` (copied from the template if missing), ensures the
`runtime/` directory exists and passes `runtime/wxnow.txt` to Direwolf using the
`-w` option. Logs are written to `direwolf.log`.

## Running rigctld

Launch `rigctld` for radio control with the helper script. Pass the rig model ID
and the `/dev/ttyUSB` device number:

```bash
./run_rigctld.sh <rig-id> <usb-num>
```

For example, to start model `503` on `/dev/ttyUSB0`:

```bash
./run_rigctld.sh 503 0
```


## Configuration

Copy the template and edit the values for your station:

```bash
cp wx-helios.conf.template wx-helios.conf
```

Telemetry sequence counters are no longer used, so the previous
`[TELEMETRY]/sequence_file` option has been removed.

The file contains APRS beacon details and Ecowitt listener settings. Install the dependencies with:

```bash
pip install -r requirements.txt
```

## Runtime directory

Scripts create writable files under `runtime/` in the project root. For example,
`ecowitt-listener.py` writes the latest APRS frame to `runtime/wxnow.txt` each
time it logs data.

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
