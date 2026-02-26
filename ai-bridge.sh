#!/bin/bash
# ai-bridge.sh - Universal AI Bridge for Rhuam
# Routes all AI outputs to Slack, triggers other AIs via webhooks
# Runs 24/7 as daemon

set -e

SLACK_WEBHOOK="https://hooks.slack.com/services/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"
CHANNEL="#ai-war-room"
STATE_DIR="$HOME/.ai-bridge"
LOG_FILE="$STATE_DIR/bridge.log"
PID_FILE="$STATE_DIR/bridge.pid"

# AI endpoint configurations (to be filled as discovered)
declare -A AI_ENDPOINTS
declare -A AI_TRIGGERS

init() {
    mkdir -p "$STATE_DIR"
    mkdir -p "$STATE_DIR/queue"
    mkdir -p "$STATE_DIR/handoffs"
    touch "$LOG_FILE"
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

send_to_slack() {
    local source="$1"
    local message="$2"
    local thread_ts="${3:-}"
    
    local payload
    if [ -n "$thread_ts" ]; then
        payload=$(jq -n \
            --arg channel "$CHANNEL" \
            --arg text "[$source] $message" \
            --arg thread_ts "$thread_ts" \
            '{channel: $channel, text: $text, thread_ts: $thread_ts}')
    else
        payload=$(jq -n \
            --arg channel "$CHANNEL" \
            --arg text "[$source] $message" \
            '{channel: $channel, text: $text}')
    fi
    
    curl -s -X POST -H 'Content-type: application/json' \
        --data "$payload" \
        "$SLACK_WEBHOOK" > /dev/null 2>&1
}

# Detect which AI produced the content
detect_source() {
    local content="$1"
    
    # Check for AI signatures in content
    if echo "$content" | grep -qi "claude\|anthropic"; then echo "claude"; return; fi
    if echo "$content" | grep -qi "gemini\|google"; then echo "gemini"; return; fi
    if echo "$content" | grep -qi "cursor"; then echo "cursor"; return; fi
    if echo "$content" | grep -qi "chatgpt\|openai"; then echo "chatgpt"; return; fi
    if echo "$content" | grep -qi "minimax"; then echo "minimax"; return; fi
    if echo "$content" | grep -qi "kimi\|moonshot"; then echo "kimi"; return; fi
    
    echo "unknown"
}

# Watch clipboard for new AI outputs (macOS and Linux)
watch_clipboard() {
    local last_clipboard=""
    
    while true; do
        local current=""
        
        if command -v pbpaste >/dev/null 2>&1; then
            current=$(pbpaste 2>/dev/null || echo "")
        elif command -v xclip >/dev/null 2>&1; then
            current=$(xclip -o -selection clipboard 2>/dev/null || echo "")
        elif command -v wl-paste >/dev/null 2>&1; then
            current=$(wl-paste 2>/dev/null || echo "")
        fi
        
        if [ -n "$current" ] && [ "$current" != "$last_clipboard" ]; then
            last_clipboard="$current"
            
            # Check if it looks like AI output (heuristics)
            if echo "$current" | grep -qE '(^Here|I can help|Based on|According to|As an AI)'; then
                local source=$(detect_source "$current")
                log "Detected $source output, sending to Slack"
                send_to_slack "$source" "$current"
                
                # Check for handoff triggers
                check_handoffs "$source" "$current"
            fi
        fi
        
        sleep 2
    done
}

# Check if output contains triggers for other AIs
check_handoffs() {
    local source="$1"
    local content="$2"
    
    # Trigger words that route to other AIs
    if echo "$content" | grep -qi "@claude\|ask claude"; then
        trigger_ai "claude" "$content"
    fi
    if echo "$content" | grep -qi "@gemini\|ask gemini"; then
        trigger_ai "gemini" "$content"
    fi
    if echo "$content" | grep -qi "@cursor\|ask cursor"; then
        trigger_ai "cursor" "$content"
    fi
    if echo "$content" | grep -qi "@kimi\|ask kimi"; then
        trigger_ai "kimi" "$content"
    fi
}

# Trigger another AI (placeholder - to be implemented per AI API)
trigger_ai() {
    local target="$1"
    local context="$2"
    
    log "Triggering $target with context"
    
    # Queue the handoff
    echo "$context" > "$STATE_DIR/handoffs/$target-$(date +%s).txt"
    
    # Notify Slack that handoff is queued
    send_to_slack "bridge" "Handoff queued: $target"
}

# Watch file system for new outputs from AIs that can write files
watch_files() {
    local watch_dirs=("$HOME/Downloads" "$HOME/Desktop" "$HOME/ai-outputs")
    
    for dir in "${watch_dirs[@]}"; do
        mkdir -p "$dir"
    done
    
    while true; do
        for dir in "${watch_dirs[@]}"; do
            find "$dir" -name "*.txt" -newer "$STATE_DIR/last_scan" 2>/dev/null | while read -r file; do
                local content=$(cat "$file" 2>/dev/null)
                if [ -n "$content" ]; then
                    local source=$(detect_source "$content")
                    log "File detected: $file from $source"
                    send_to_slack "$source" "$content"
                    mv "$file" "$STATE_DIR/processed/"
                fi
            done
        done
        
        touch "$STATE_DIR/last_scan"
        sleep 5
    done
}

# Consensus command - aggregates multiple AI opinions
consensus() {
    local question="$1"
    
    log "Starting consensus for: $question"
    
    # Send to all AIs
    send_to_slack "bridge" "CONSENSUS REQUEST: $question"
    send_to_slack "bridge" "@channel All AIs please respond"
    
    # Wait and collect (manual for now, automated later)
    echo "Collecting responses... Check Slack thread"
}

# Daemon mode
daemon() {
    init
    
    if [ -f "$PID_FILE" ]; then
        local old_pid=$(cat "$PID_FILE")
        if kill -0 "$old_pid" 2>/dev/null; then
            log "Bridge already running (PID: $old_pid)"
            exit 1
        fi
    fi
    
    echo $$ > "$PID_FILE"
    log "Bridge daemon started (PID: $$)"
    
    # Start watchers in background
    watch_clipboard &
    watch_files &
    
    wait
}

# Commands
case "${1:-daemon}" in
    start|daemon)
        daemon
        ;;
    stop)
        if [ -f "$PID_FILE" ]; then
            kill $(cat "$PID_FILE") 2>/dev/null && rm -f "$PID_FILE"
            log "Bridge stopped"
        fi
        ;;
    send)
        send_to_slack "${2:-manual}" "${3:-test message}"
        ;;
    consensus)
        consensus "${2:-What should we build?}"
        ;;
    status)
        if [ -f "$PID_FILE" ] && kill -0 $(cat "$PID_FILE") 2>/dev/null; then
            echo "Bridge running (PID: $(cat $PID_FILE))"
        else
            echo "Bridge not running"
        fi
        ;;
    *)
        echo "Usage: $0 {start|stop|send|consensus|status}"
        exit 1
        ;;
esac
