#!/bin/bash
# For Testing, this can be used to run hubTelemetry in a loop
# For deployment, use cron to run hubTelemetry
# 
while true
do
    echo "Running telemetry beacon at $(date)"
    python3 ./hubTelemetry.py
    sleep 3600  # Run every 60 minutes
done

