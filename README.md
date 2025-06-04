# KF0TKE APRS Telemetry Beacon

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
- `wx-heliox solar-power controller` and `wx-heliox solar-power controller telemetry`
- `wx-heliox solar-panels` and `wx-heliox solar-panels telemetry`

## Features

- APRS position and telemetry embedded in a human-readable comment
- Configuration via an INI file
- Works with the Direwolf KISS interface
- Portable across hardware platforms
- Proven symbol handling, beacon loop and telemetry extraction

## Requirements

- Debian / Ubuntu / Raspberry Pi OS
- Python 3.x
- `psutil` Python package

## Configuration

Copy the template and edit the values for your station:

```bash
cp hubTelemetry.conf.template hubTelemetry.conf
```

Set callsign, coordinates, symbol table, path and destination. Install the dependencies with:

```bash
pip3 install psutil
```

## License

This project is licensed under the GNU General Public License version 2. See [LICENSE](LICENSE) for details.
