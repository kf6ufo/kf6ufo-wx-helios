#!/bin/bash
# Launch the Direwolf TNC using the wx-helios-direwolf build

set -e

CONF="direwolf.conf"
RUNTIME_DIR="runtime"
WXNOW="$RUNTIME_DIR/wxnow.txt"

ENABLED=$(python3 - <<'EOF'
import config
print("yes" if config.load_direwolf_config().get("enabled", True) else "no")
EOF
)
if [ "$ENABLED" != "yes" ]; then
    echo "Direwolf disabled in configuration" >&2
    exit 0
fi

# If the local configuration doesn't exist, create it from the template
if [ ! -f "$CONF" ]; then
    cp direwolf.conf.template "$CONF"
fi

# Ensure runtime directory exists for wxnow file
mkdir -p "$RUNTIME_DIR"

# Run Direwolf with the configuration, wxnow file and log to direwolf.log
exec "$(dirname "$0")/external/direwolf/build/src/direwolf" -c "$CONF" -l direwolf.log -w "$WXNOW"
