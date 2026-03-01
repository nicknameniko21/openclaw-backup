#!/bin/bash
# Post-start command for Codespace
# Runs every time Codespace starts

echo "Starting Kimi Claw automation services..."

# Start AI Bridge file watcher
if [ -f /workspaces/openclaw-backup/ai-bridge-watcher.sh ]; then
    echo "Starting AI Bridge..."
    nohup bash /workspaces/openclaw-backup/ai-bridge-watcher.sh > /tmp/ai-bridge.log 2>&1 &
fi

# Check for pending work
cd /workspaces/openclaw-backup

# Run Microsoft Rewards if accounts configured
if [ -f rewards/accounts.json ]; then
    VALID=$(jq '[.accounts[] | select(.email | contains("example.com") | not)] | length' rewards/accounts.json)
    if [ "$VALID" -gt 0 ]; then
        echo "Running Microsoft Rewards..."
        cd rewards && python3 rewards_bot.py > /tmp/rewards.log 2>&1 &
    fi
fi

# Keep-alive ping (prevents Codespace from sleeping)
(
    while true; do
        sleep 300
        echo "$(date): Keep-alive ping" >> /tmp/codespace-alive.log
        git fetch origin > /dev/null 2>&1
    done
) &

echo "All services started!"
echo "Logs: /tmp/ai-bridge.log /tmp/rewards.log /tmp/codespace-alive.log"
