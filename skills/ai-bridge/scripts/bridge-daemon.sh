#!/bin/bash
# bridge-daemon.sh - 24/7 AI bridge daemon
# Monitors clipboard, files, routes to Slack

set -e

CONFIG_DIR="${HOME}/.ai-bridge"
STATE_DIR="${CONFIG_DIR}/state"
LOG_FILE="${STATE_DIR}/bridge.log"
PID_FILE="${STATE_DIR}/daemon.pid"
CONFIG_FILE="${CONFIG_DIR}/config.json"
QUEUE_DIR="${STATE_DIR}/queue"
THREADS_DIR="${STATE_DIR}/threads"

# Load config
SLACK_WEBHOOK=$(jq -r '.slack_webhook // empty' "$CONFIG_FILE" 2>/dev/null || echo "")
CHANNEL=$(jq -r '.channel // "#ai-war-room"' "$CONFIG_FILE" 2>/dev/null || echo "#ai-war-room")

init() {
    mkdir -p "$STATE_DIR" "$QUEUE_DIR" "$THREADS_DIR" ~/ai-outputs
    touch "$LOG_FILE"
    
    # Default config if missing
    if [ ! -f "$CONFIG_FILE" ]; then
        cat > "$CONFIG_FILE" << 'EOF'
{
  "slack_webhook": "",
  "channel": "#ai-war-room",
  "ai_endpoints": {},
  "trigger_words": {
    "claude": ["@claude", "→claude", "ask claude"],
    "gemini": ["@gemini", "→gemini", "ask gemini"],
    "cursor": ["@cursor", "→cursor", "ask cursor"],
    "kimi": ["@kimi", "→kimi", "ask kimi"],
    "chatgpt": ["@chatgpt", "→chatgpt", "ask chatgpt"],
    "minimax": ["@minimax", "→minimax", "ask minimax"]
  },
  "consensus_keyword": "/consensus"
}
EOF
    fi
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_slack() {
    local source="$1"
    local text="$2"
    local thread_ts="${3:-}"
    
    [ -z "$SLACK_WEBHOOK" ] && return
    
    local payload
    if [ -n "$thread_ts" ]; then
        payload=$(jq -n --arg ch "$CHANNEL" --arg txt "[$source] $text" --arg ts "$thread_ts" '{channel: $ch, text: $txt, thread_ts: $ts}')
    else
        payload=$(jq -n --arg ch "$CHANNEL" --arg txt "[$source] $text" '{channel: $ch, text: $txt}')
    fi
    
    curl -s -X POST -H 'Content-type: application/json' --data "$payload" "$SLACK_WEBHOOK" > /dev/null 2>&1 || true
}

# Detect AI source from content signatures
detect_source() {
    local content="$1"
    
    # Check for explicit signatures first
    if echo "$content" | grep -qiE '(claude|anthropic).*assistant'; then echo "claude"; return; fi
    if echo "$content" | grep -qiE '(gemini|google).*assistant'; then echo "gemini"; return; fi
    if echo "$content" | grep -qi 'cursor'; then echo "cursor"; return; fi
    if echo "$content" | grep -qiE '(chatgpt|openai)'; then echo "chatgpt"; return; fi
    if echo "$content" | grep -qi 'minimax'; then echo "minimax"; return; fi
    if echo "$content" | grep -qiE '(kimi|moonshot)'; then echo "kimi"; return; fi
    
    # Heuristics based on response patterns
    if echo "$content" | grep -qE "^Here.*(is|are)|^I can( certainly)? (help|assist)|^I'd be (happy|glad) to"; then echo "claude"; return; fi
    if echo "$content" | grep -qiE 'gemini|bard|google.*ai'; then echo "gemini"; return; fi
    
    echo "unknown"
}

# Check for trigger words and queue handoffs
check_triggers() {
    local source="$1"
    local content="$2"
    local timestamp=$(date +%s)
    
    # Load trigger words from config
    local triggers=$(jq -r '.trigger_words // {}' "$CONFIG_FILE" 2>/dev/null || echo '{}')
    
    # Check each AI's trigger words
    for target in claude gemini cursor kimi chatgpt minimax; do
        local words=$(echo "$triggers" | jq -r ".${target}[]?" 2>/dev/null)
        for word in $words; do
            if echo "$content" | grep -qi "$word"; then
                log "TRIGGER: $source → $target"
                queue_handoff "$source" "$target" "$content" "$timestamp"
                send_slack "bridge" "🔄 Handoff queued: $source → $target"
            fi
        done
    done
    
    # Check for consensus
    local consensus_kw=$(jq -r '.consensus_keyword // "/consensus"' "$CONFIG_FILE")
    if echo "$content" | grep -qi "^$consensus_kw"; then
        local question=$(echo "$content" | sed "s/$consensus_kw//i" | xargs)
        log "CONSENSUS: $question"
        queue_consensus "$source" "$question" "$timestamp"
        send_slack "bridge" "📊 Consensus requested by $source: $question"
    fi
}

# Queue a handoff for processing
queue_handoff() {
    local from="$1"
    local to="$2"
    local content="$3"
    local timestamp="$4"
    
    local queue_file="${QUEUE_DIR}/handoff-${timestamp}-${from}-${to}.json"
    
    jq -n \
        --arg from "$from" \
        --arg to "$to" \
        --arg content "$content" \
        --arg timestamp "$timestamp" \
        '{type: "handoff", from: $from, to: $to, content: $content, timestamp: $timestamp, status: "pending"}' \
        > "$queue_file"
}

# Queue consensus request
queue_consensus() {
    local from="$1"
    local question="$2"
    local timestamp="$3"
    
    local queue_file="${QUEUE_DIR}/consensus-${timestamp}.json"
    
    jq -n \
        --arg from "$from" \
        --arg question "$question" \
        --arg timestamp "$timestamp" \
        '{type: "consensus", from: $from, question: $question, timestamp: $timestamp, responses: {}, status: "collecting"}' \
        > "$queue_file"
}

# Watch clipboard for new content
watch_clipboard() {
    local last_clipboard=""
    
    log "Starting clipboard watcher..."
    
    while true; do
        local current=""
        
        # macOS
        if command -v pbpaste >/dev/null 2>&1; then
            current=$(pbpaste 2>/dev/null || echo "")
        # Linux X11
        elif command -v xclip >/dev/null 2>&1; then
            current=$(xclip -o -selection clipboard 2>/dev/null || echo "")
        # Linux Wayland
        elif command -v wl-paste >/dev/null 2>&1; then
            current=$(wl-paste 2>/dev/null || echo "")
        fi
        
        if [ -n "$current" ] && [ "$current" != "$last_clipboard" ]; then
            last_clipboard="$current"
            
            # Quick heuristic: does this look like AI output?
            if echo "$current" | grep -qE '(^Here|^I can|^Based on|^According to|^As an AI|^Let me|^I think|^I believe|^In my opinion|assistant|AI|model)'; then
                local source=$(detect_source "$current")
                log "Detected AI output from: $source"
                send_slack "$source" "$current"
                check_triggers "$source" "$current"
            fi
        fi
        
        sleep 1
    done
}

# Watch file drops
watch_files() {
    log "Starting file watcher..."
    
    local watch_dirs=("$HOME/ai-outputs" "$HOME/Downloads" "$HOME/Desktop")
    
    for dir in "${watch_dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    touch "$STATE_DIR/last_file_scan"
    
    while true; do
        for dir in "${watch_dirs[@]}"; do
            find "$dir" -type f -newer "$STATE_DIR/last_file_scan" 2>/dev/null | while read -r file; do
                # Skip if already processed
                local basename=$(basename "$file")
                if [ -f "$STATE_DIR/processed/$basename" ]; then continue; fi
                
                local content=$(cat "$file" 2>/dev/null | head -c 10000)
                if [ -n "$content" ]; then
                    local source=$(detect_source "$content")
                    log "File detected: $file from $source"
                    send_slack "$source" "📄 File: $basename
$content"
                    check_triggers "$source" "$content"
                    
                    # Mark as processed
                    mkdir -p "$STATE_DIR/processed"
                    touch "$STATE_DIR/processed/$basename"
                fi
            done
        done
        
        touch "$STATE_DIR/last_file_scan"
        sleep 3
    done
}

# Process queue (handoffs, consensus)
process_queue() {
    log "Starting queue processor..."
    
    while true; do
        for queue_file in "$QUEUE_DIR"/*.json; do
            [ -f "$queue_file" ] || continue
            
            local type=$(jq -r '.type' "$queue_file")
            local status=$(jq -r '.status' "$queue_file")
            
            [ "$status" != "pending" ] && [ "$status" != "collecting" ] && continue
            
            if [ "$type" = "handoff" ]; then
                local to=$(jq -r '.to' "$queue_file")
                local content=$(jq -r '.content' "$queue_file")
                
                # Try to deliver to target AI
                if deliver_to_ai "$to" "$content"; then
                    jq '.status = "delivered"' "$queue_file" > "${queue_file}.tmp" && mv "${queue_file}.tmp" "$queue_file"
                    log "Delivered to $to"
                fi
            elif [ "$type" = "consensus" ]; then
                # Check if we have enough responses
                local response_count=$(jq '.responses | length' "$queue_file")
                if [ "$response_count" -ge 3 ]; then
                    # Generate consensus summary
                    generate_consensus "$queue_file"
                fi
            fi
        done
        
        sleep 5
    done
}

# Deliver content to target AI
deliver_to_ai() {
    local target="$1"
    local content="$2"
    
    # Get endpoint from config
    local endpoint=$(jq -r ".ai_endpoints.${target} // empty" "$CONFIG_FILE")
    
    if [ -z "$endpoint" ]; then
        log "No endpoint configured for $target"
        return 1
    fi
    
    # Handle different endpoint types
    if [[ "$endpoint" == file://* ]]; then
        # File-based delivery (for Cursor, etc.)
        local filepath="${endpoint#file://}"
        echo "$content" > "$filepath/bridge-inbox-$(date +%s).txt"
        return 0
    elif [[ "$endpoint" == http* ]]; then
        # HTTP webhook
        curl -s -X POST -H 'Content-type: application/json' \
            --data "{\"source\": \"bridge\", \"content\": $(echo "$content" | jq -Rs .)}" \
            "$endpoint" > /dev/null 2>&1 && return 0
        return 1
    fi
    
    return 1
}

# Generate consensus from multiple responses
generate_consensus() {
    local queue_file="$1"
    
    log "Generating consensus..."
    
    # Mark as processing
    jq '.status = "processing"' "$queue_file" > "${queue_file}.tmp" && mv "${queue_file}.tmp" "$queue_file"
    
    # Extract responses
    local question=$(jq -r '.question' "$queue_file")
    local responses=$(jq -r '.responses | to_entries | map("\(.key): \(.value)") | join("\n---\n")' "$queue_file")
    
    # Send to Slack for manual review (auto-consensus is hard)
    send_slack "consensus" "📊 CONSENSUS for: $question

Responses collected:
$responses

[Human review needed for synthesis]"
    
    jq '.status = "complete"' "$queue_file" > "${queue_file}.tmp" && mv "${queue_file}.tmp" "$queue_file"
}

# Main daemon
daemon() {
    init
    
    # Check if already running
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE" 2>/dev/null)
        if [ -n "$old_pid" ] && kill -0 "$old_pid" 2>/dev/null; then
            log "Daemon already running (PID: $old_pid)"
            exit 1
        fi
    fi
    
    echo $$ > "$PID_FILE"
    log "=== AI Bridge Daemon Started (PID: $$) ==="
    
    # Trap signals for clean shutdown
    trap 'log "Daemon stopping..."; rm -f "$PID_FILE"; exit 0' INT TERM
    
    # Start all watchers
    watch_clipboard &
    watch_files &
    process_queue &
    
    # Keep main process alive
    wait
}

# CLI commands
case "${1:-start}" in
    start|daemon)
        daemon
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null && rm -f "$PID_FILE"
            log "Daemon stopped"
        else
            echo "Daemon not running"
        fi
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Running (PID: $(cat $PID_FILE))"
            echo "Log: $LOG_FILE"
            echo "Queue: $(ls -1 $QUEUE_DIR/*.json 2>/dev/null | wc -l) items"
        else
            echo "Not running"
            rm -f "$PID_FILE"
        fi
        ;;
    config)
        cat "$CONFIG_FILE" 2>/dev/null || echo "No config found"
        ;;
    log)
        tail -f "$LOG_FILE"
        ;;
    test)
        init
        send_slack "test" "Bridge test message from $(hostname)"
        echo "Test sent to Slack"
        ;;
    *)
        echo "Usage: $(basename $0) {start|stop|status|config|log|test}"
        exit 1
        ;;
esac
