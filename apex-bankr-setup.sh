#!/bin/bash
# Apex + Bankr Signals Integration
# Publishes Apex trading signals to Bankr with blockchain verification

CONFIG_FILE="/root/.openclaw/workspace/.bankr/config.json"
LOG_FILE="/root/.openclaw/workspace/memory/apex-bankr.log"

mkdir -p "$(dirname "$CONFIG_FILE")"
mkdir -p "$(dirname "$LOG_FILE")"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Check if API key exists
if [ ! -f "$CONFIG_FILE" ]; then
    log "Bankr config not found. Creating template..."
    cat > "$CONFIG_FILE" << 'EOF'
{
  "apiKey": "",
  "apiUrl": "https://api.bankr.bot",
  "wallet": "",
  "providerName": "ApexTrader",
  "registered": false
}
EOF
    log "Template created at $CONFIG_FILE"
    log "ACTION NEEDED: Add Bankr API key (bk_...) to config"
    exit 1
fi

API_KEY=$(jq -r '.apiKey // empty' "$CONFIG_FILE")
if [ -z "$API_KEY" ]; then
    log "ERROR: No API key in config"
    log "Get API key from https://bankr.bot/api"
    exit 1
fi

# Get wallet address from Bankr
log "Fetching wallet from Bankr..."
WALLET=$(curl -s -X POST "https://api.bankr.bot/agent/prompt" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d '{"prompt": "What is my wallet address?"}' | jq -r '.result // empty')

if [ -z "$WALLET" ] || [ "$WALLET" = "null" ]; then
    log "ERROR: Could not get wallet address"
    exit 1
fi

log "Wallet: $WALLET"

# Update config with wallet
jq --arg wallet "$WALLET" '.wallet = $wallet' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"

# Check if registered as provider
REGISTERED=$(jq -r '.registered // false' "$CONFIG_FILE")
if [ "$REGISTERED" != "true" ]; then
    log "Registering as Bankr Signals provider..."
    
    TIMESTAMP=$(date +%s)
    MESSAGE="bankr-signals:register:$WALLET:$TIMESTAMP"
    
    # Sign registration message
    SIGN_RESULT=$(curl -s -X POST "https://api.bankr.bot/agent/sign" \
        -H "X-API-Key: $API_KEY" \
        -H "Content-Type: application/json" \
        -d "{\"signatureType\": \"personal_sign\", \"message\": \"$MESSAGE\"}")
    
    SIGNATURE=$(echo "$SIGN_RESULT" | jq -r '.signature // empty')
    
    if [ -z "$SIGNATURE" ] || [ "$SIGNATURE" = "null" ]; then
        log "ERROR: Could not sign registration message"
        exit 1
    fi
    
    # Register provider
    REGISTER_RESULT=$(curl -s -X POST "https://bankrsignals.com/api/providers/register" \
        -H "Content-Type: application/json" \
        -d "{
            \"address\": \"$WALLET\",
            \"name\": \"ApexTrader\",
            \"bio\": \"Autonomous AI trading agent using Apex Trading System\",
            \"chain\": \"base\",
            \"agent\": \"openclaw\",
            \"message\": \"$MESSAGE\",
            \"signature\": \"$SIGNATURE\"
        }")
    
    if echo "$REGISTER_RESULT" | grep -q "error"; then
        log "Registration result: $REGISTER_RESULT"
    else
        log "Successfully registered as provider"
        jq '.registered = true' "$CONFIG_FILE" > "${CONFIG_FILE}.tmp" && mv "${CONFIG_FILE}.tmp" "$CONFIG_FILE"
    fi
fi

log "Apex-Bankr integration ready"
log "To publish signals, call: ./publish-signal.sh LONG ETH 2650.00 5"
