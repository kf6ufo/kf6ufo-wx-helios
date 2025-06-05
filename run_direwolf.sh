#!/bin/bash
# Launch the Direwolf TNC using the wx-helios-direwolf build

set -e

CONF="direwolf.conf"

# If the local configuration doesn't exist, create it from the template
if [ ! -f "$CONF" ]; then
    cp direwolf.conf.template "$CONF"
fi

# Run Direwolf with the configuration and log to direwolf.log
exec direwolf -c "$CONF" -l direwolf.log
