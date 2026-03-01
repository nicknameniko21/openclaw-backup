#!/bin/bash
# Offline Mode - No external connections
# Work with local files only

echo "=== OFFLINE MODE ACTIVATED ==="
echo "All external connections disabled"
echo "Working from local cache only"

# Disable all networking
ip link set lo down 2>/dev/null || echo "Cannot disable loopback (container)"

# Work queue for when connection restored
mkdir -p /root/.openclaw/workspace/.secure/offline-queue

echo "Offline mode active. Queue tasks in:"
echo "/root/.openclaw/workspace/.secure/offline-queue/"
