# KF0TKE APRS Telemetry Beacon

A simple, hardware-agnostic APRS telemetry beacon system for Raspberry Pi, laptops, and field stations.  This is a holding place repo until I get a vanity call sign for this project, but everything is still working if it is in the repo.

This is the "hub" part of a solar-powered APRS RF-Weather station project for amateur radio.

## Features

- APRS position + telemetry in human-readable comment format
- Configurable via INI file
- Fully compatible with Direwolf KISS interface
- Fully portable across hardware platforms (Pi, laptop, field box)
- Field-tested symbol handling, beacon loop, and telemetry extraction

## Requirements

- Debian / Ubuntu / Raspberry Pi OS
- Python 3.x
- psutil Python package

## Configuration
- Edit hubTelemetry.conf to set: Callsign, lat/lon, symbol, path, and destination
- Edit hubTelemetry.conf to set: Symbol table ("primary" or "secondary")
- Copy the template file to create your deployment config:

```bash
cp hubTelemetry.conf.template hubTelemetry.conf
```

- Install psutil:

```bash
pip3 install psutil
```
