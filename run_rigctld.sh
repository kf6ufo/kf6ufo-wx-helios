#!/bin/bash
# Start rigctld with the specified rig model and serial adapter

set -e

if [ "$#" -ne 2 ]; then
    echo "Usage: $0 <rig-id> <ttyUSB number>" >&2
    echo "Example: $0 503 0" >&2
    exit 1
fi

RIG_ID="$1"
USB_NUM="$2"

exec rigctld -m "$RIG_ID" -r "/dev/ttyUSB${USB_NUM}" -t 4531
