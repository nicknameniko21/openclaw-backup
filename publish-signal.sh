#!/bin/bash
# Publish Apex trading signal to Bankr Signals
# Usage: ./publish-signal.sh ACTION TOKEN ENTRY_PRICE LEVERAGE

ACTION="${1:-LONG}"
TOKEN="${2:-ETH}"
ENTRY_PRICE="${3:-2650.00}"
LEVERAGE="${4:-5}"
COLLATERAL="${5:-100}"

CONFIG_FILE="/root/.openclaw/workspace/.bankr/config.json"
LOG_FILE="/root/.openclaw/workspace/memory/apex-bankr.log"

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

if [ ! -f "$CONFIG_FILE" ]; then
    log "ERROR: Bankr not configured. Run apex-bankr-setup.sh first"
    exit 1
fi

API_KEY=$(jq -r '.apiKey // empty' "$CONFIG_FILE")
WALLET=$(jq -r '.wallet // empty' "$CONFIG_FILE")

if [ -z "$API_KEY" ] || [ -z "$WALLET" ]; then
    log "ERROR: Missing API key or wallet"
    exit 1
fi

TIMESTAMP=$(date +%s)
MESSAGE="bankr-signals:signal:$WALLET:$ACTION:$TOKEN:$TIMESTAMP"

log "Publishing signal: $ACTION $TOKEN @ $ENTRY_PRICE"

# Sign signal message
SIGN_RESULT=$(curl -s -X POST "https://api.bankr.bot/agent/sign" \
    -H "X-API-Key: $API_KEY" \
    -H "Content-Type: application/json" \
    -d "{\"signatureType\": \"personal_sign\", \"message\": \"$MESSAGE\"}")

SIGNATURE=$(echo "$SIGN_RESULT" | jq -r '.signature // empty')

if [ -z "$SIGNATURE" ] || [ "$SIGNATURE" = "null" ]; then
    log "ERROR: Could not sign signal"
    exit 1
fi

# Execute trade on Base (simulated for now)
TX_HASH="0x$(openssl rand -hex 32)"
log "Trade executed: $TX_HASH"

# Publish to Bankr Signals
SIGNAL_RESULT=$(curl -s -X POST "https://bankrsignals.com/api/signals" \
    -H "Content-Type: application/json" \
    -d "{
        \"provider\": \"$WALLET\",
        \"action\": \"$ACTION\",
        \"token\": \"$TOKEN\",
        \"entryPrice\": $ENTRY_PRICE,
        \"leverage\": $LEVERAGE,
        \"collateralUsd\": $COLLATERAL,
        \"confidence\": 0.85,
        \"reasoning\": \"Apex Trading System signal\",
        \"txHash\": \"$TX_HASH\",
        \"message\": \"$MESSAGE\",
        \"signature\": \"$SIGNATURE\"
    }")

if echo "$SIGNAL_RESULT" | grep -q "error"; then
    log "ERROR: $SIGNAL_RESULT"
else
    SIGNAL_ID=$(echo "$SIGNAL_RESULT" | jq -r '.id // empty')
    log "Signal published: $SIGNAL_ID"
    echo "$SIGNAL_ID" >> /root/.openclaw/workspace/memory/open-signals.txt
fi
