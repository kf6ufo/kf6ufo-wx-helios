#!/bin/bash
# Start rigctld with the specified rig model and serial adapter

set -e

usage() {
    echo "Usage: $0 <rig-id> <ttyUSB number>" >&2
    echo "       $0" >&2
    echo "Example: $0 503 0" >&2
    exit 1
}

if [ "$#" -eq 2 ]; then
    RIG_ID="$1"
    USB_NUM="$2"
elif [ "$#" -eq 0 ]; then
    RIG_ID=$(python3 -c 'import config; print(config.load_rig_config().get("rig_id", ""))')
    USB_NUM=$(python3 -c 'import config; print(config.load_rig_config().get("usb_num", ""))')
    if [ -z "$RIG_ID" ] || [ -z "$USB_NUM" ]; then
        echo "Rig settings not found in configuration" >&2
        usage
    fi
else
    usage
fi

exec rigctld -m "$RIG_ID" -r "/dev/ttyUSB${USB_NUM}" -t 4531
