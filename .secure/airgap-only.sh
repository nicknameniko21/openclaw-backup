#!/bin/bash
# AIR-GAP ONLY MODE
# No network. Local files only.

# Disable all networking
ip link set eth0 down 2>/dev/null || true
ip link set wlan0 down 2>/dev/null || true

# Work from airgap only
cd /root/.openclaw/workspace/.secure/airgap

# Local automation only
while true; do
    # Process local files
    # No external connections
    # Git commits disabled
    sleep 60
done
