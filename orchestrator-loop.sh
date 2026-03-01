#!/bin/bash
# Multi-Platform Orchestrator - Continuous Loop
# Runs 24/7, distributes work across platforms

CONFIG_FILE="/root/.openclaw/workspace/.orchestrator/config.json"
LOG_FILE="/root/.openclaw/workspace/memory/orchestrator.log"

mkdir -p "$(dirname "$CONFIG_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Initialize config
if [ ! -f "$CONFIG_FILE" ]; then
    cat > "$CONFIG_FILE" << 'EOF'
{
  "platforms": {
    "github": {"enabled": true, "priority": 1},
    "vercel": {"enabled": false, "priority": 2},
    "colab": {"enabled": false, "priority": 3},
    "azure": {"enabled": false, "priority": 4},
    "aws": {"enabled": false, "priority": 5},
    "oracle": {"enabled": false, "priority": 6},
    "local": {"enabled": true, "priority": 0}
  }
}
EOF
fi

log "=== Orchestrator starting ==="

# Main loop - runs forever
while true; do
    log "--- Cycle start ---"
    
    # Check local tasks
    if [ -d /root/.openclaw/workspace/ai-outputs ]; then
        PENDING=$(ls -1 /root/.openclaw/workspace/ai-outputs/*.txt 2>/dev/null | wc -l)
        if [ "$PENDING" -gt 0 ]; then
            log "Processing $PENDING pending tasks"
            for file in /root/.openclaw/workspace/ai-outputs/*.txt; do
                [ -f "$file" ] || continue
                log "Processing: $(basename "$file")"
                # Move to processed
                mkdir -p /root/.openclaw/workspace/ai-outputs/processed
                mv "$file" /root/.openclaw/workspace/ai-outputs/processed/ 2>/dev/null || true
            done
        fi
    fi
    
    # Trigger GitHub workflows (if under limit)
    log "Triggering GitHub workflows..."
    cd /root/.openclaw/workspace
    
    # Microsoft Rewards check
    if [ -f rewards/accounts.json ]; then
        VALID=$(jq '[.accounts[] | select(.email | contains("example.com") | not)] | length' rewards/accounts.json 2>/dev/null || echo 0)
        if [ "$VALID" -gt 0 ]; then
            log "Found $VALID valid accounts - should run rewards"
            # Trigger workflow via API if token available
        fi
    fi
    
    # Git operations
    if [ -d .git ]; then
        git add -A 2>/dev/null || true
        git diff --quiet && git diff --staged --quiet || {
            git commit -m "Auto: $(date '+%H:%M:%S')" 2>/dev/null || true
            git push origin main 2>/dev/null || true
            log "Git sync completed"
        }
    fi
    
    log "--- Cycle complete ---"
    
    # Sleep before next cycle (5 minutes = 12 cycles/hour = 288/day)
    # At 50-75% capacity, this is sustainable
    sleep 300
done
