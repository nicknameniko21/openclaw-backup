#!/bin/bash
# Secure Connector - War Mode
# Only connects to pre-approved endpoints

ALLOWED_ENDPOINTS=(
    "github.com:443"
    "api.github.com:443"
    "raw.githubusercontent.com:443"
)

LOG_FILE="/root/.openclaw/workspace/.secure/connection.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG_FILE"
}

is_allowed() {
    local host="$1"
    local port="$2"
    for endpoint in "${ALLOWED_ENDPOINTS[@]}"; do
        if [[ "$endpoint" == "$host:$port" ]]; then
            return 0
        fi
    done
    return 1
}

# Main connector loop
while true; do
    # Check for outbound requests in queue
    for req in /root/.openclaw/workspace/.secure/outbound/*.req; do
        [ -f "$req" ] || continue
        
        host=$(cat "$req" | grep "^HOST:" | cut -d: -f2- | tr -d ' ')
        port=$(cat "$req" | grep "^PORT:" | cut -d: -f2 | tr -d ' ')
        
        if is_allowed "$host" "$port"; then
            log "ALLOWED: $host:$port"
            # Execute request
            bash "$req" > "${req}.out" 2>&1
            mv "$req" "${req}.completed"
        else
            log "BLOCKED: $host:$port"
            mv "$req" "${req}.blocked"
        fi
    done
    
    sleep 10
done
