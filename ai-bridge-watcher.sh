#!/bin/bash
# AI Bridge file watcher - runs without Slack webhook
# Watches ~/ai-outputs/ for files from other AIs

WATCH_DIR="/root/.openclaw/workspace/ai-outputs"
LOG_FILE="/root/.openclaw/workspace/memory/ai-bridge.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

log "AI Bridge File Watcher started"
log "Watching: $WATCH_DIR"

# Process existing files
find "$WATCH_DIR" -type f -name "*.txt" -o -name "*.md" 2>/dev/null | while read -r file; do
    basename=$(basename "$file")
    source=$(echo "$basename" | cut -d'-' -f1)
    log "Found: $basename from $source"
    
    # Check for trigger words
    content=$(cat "$file" 2>/dev/null)
    if echo "$content" | grep -qiE "@kimi|→kimi|ask kimi"; then
        log "TRIGGER: Routing to Kimi"
        cp "$file" "$WATCH_DIR/kimi-inbox/"
    fi
    if echo "$content" | grep -qiE "@claude|→claude|ask claude"; then
        log "TRIGGER: Routing to Claude"
        cp "$file" "$WATCH_DIR/claude-inbox/"
    fi
    if echo "$content" | grep -qiE "@consensus|/consensus"; then
        log "CONSENSUS: Collecting responses"
        cp "$file" "$WATCH_DIR/consensus/"
    fi
done

log "Initial scan complete. Running inotifywait for new files..."

# Watch for new files (if inotifywait available)
if command -v inotifywait >/dev/null 2>&1; then
    inotifywait -m -r -e create --format '%w%f' "$WATCH_DIR" 2>/dev/null | while read -r file; do
        log "New file: $file"
        # Process triggers...
    done
else
    log "inotifywait not available, using polling"
    while true; do
        sleep 5
    done
fi
