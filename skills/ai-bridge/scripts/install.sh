#!/bin/bash
# install.sh - One-command installer for AI Bridge

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILL_DIR="$(dirname "$SCRIPT_DIR")"
INSTALL_DIR="${HOME}/.ai-bridge"
BIN_DIR="/usr/local/bin"

echo "=== AI Bridge Installer ==="
echo

# Check dependencies
check_deps() {
    local missing=()
    
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v curl >/dev/null 2>&1 || missing+=("curl")
    
    if [ ${#missing[@]} -gt 0 ]; then
        echo "Missing dependencies: ${missing[*]}"
        echo "Install with:"
        echo "  macOS: brew install ${missing[*]}"
        echo "  Ubuntu/Debian: sudo apt-get install ${missing[*]}"
        echo "  CentOS/RHEL: sudo yum install ${missing[*]}"
        exit 1
    fi
}

# Install files
install_files() {
    echo "Installing AI Bridge..."
    
    # Create directories
    mkdir -p "$INSTALL_DIR"/{state,state/queue,state/threads,state/processed,connectors}
    
    # Copy scripts
    cp "$SCRIPT_DIR/bridge-daemon.sh" "$INSTALL_DIR/"
    chmod +x "$INSTALL_DIR/bridge-daemon.sh"
    
    # Create symlink
    if [ -w "$BIN_DIR" ]; then
        ln -sf "$INSTALL_DIR/bridge-daemon.sh" "$BIN_DIR/ai-bridge"
    else
        echo "Warning: Cannot write to $BIN_DIR"
        echo "Add to your PATH: export PATH=\"$INSTALL_DIR:\$PATH\""
        ln -sf "$INSTALL_DIR/bridge-daemon.sh" "$INSTALL_DIR/ai-bridge"
    fi
    
    # Create config
    if [ ! -f "$INSTALL_DIR/config.json" ]; then
        cat > "$INSTALL_DIR/config.json" << 'EOF'
{
  "slack_webhook": "https://hooks.slack.com/services/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",
  "channel": "#ai-war-room",
  "ai_endpoints": {
    "claude": "",
    "gemini": "",
    "cursor": "file:///tmp/cursor-bridge",
    "kimi": "",
    "chatgpt": "",
    "minimax": ""
  },
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
    
    # Create cursor inbox dir
    mkdir -p /tmp/cursor-bridge
    
    echo "✓ Installed to $INSTALL_DIR"
}

# Create systemd service (Linux)
install_systemd() {
    if command -v systemctl >/dev/null 2>&1; then
        echo "Creating systemd service..."
        
        cat > /tmp/ai-bridge.service << EOF
[Unit]
Description=AI Bridge Daemon
After=network.target

[Service]
Type=simple
User=$USER
ExecStart=$INSTALL_DIR/bridge-daemon.sh start
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF
        
        echo "To enable auto-start:"
        echo "  sudo mv /tmp/ai-bridge.service /etc/systemd/system/"
        echo "  sudo systemctl enable ai-bridge"
        echo "  sudo systemctl start ai-bridge"
    fi
}

# Create launchd plist (macOS)
install_launchd() {
    if [ "$(uname)" = "Darwin" ]; then
        echo "Creating launchd service..."
        
        cat > ~/Library/LaunchAgents/com.ai-bridge.daemon.plist << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.ai-bridge.daemon</string>
    <key>ProgramArguments</key>
    <array>
        <string>$INSTALL_DIR/bridge-daemon.sh</string>
        <string>start</string>
    </array>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
    <key>StandardOutPath</key>
    <string>$INSTALL_DIR/state/stdout.log</string>
    <key>StandardErrorPath</key>
    <string>$INSTALL_DIR/state/stderr.log</string>
</dict>
</plist>
EOF
        
        echo "To enable auto-start:"
        echo "  launchctl load ~/Library/LaunchAgents/com.ai-bridge.daemon.plist"
    fi
}

# Main
main() {
    check_deps
    install_files
    
    if [ "$(uname)" = "Darwin" ]; then
        install_launchd
    else
        install_systemd
    fi
    
    echo
    echo "=== Installation Complete ==="
    echo
    echo "Commands:"
    echo "  ai-bridge start    - Start daemon"
    echo "  ai-bridge stop     - Stop daemon"
    echo "  ai-bridge status   - Check status"
    echo "  ai-bridge log      - View logs"
    echo "  ai-bridge test     - Test Slack connection"
    echo
    echo "Config: $INSTALL_DIR/config.json"
    echo
    echo "Next steps:"
    echo "1. Edit config: nano $INSTALL_DIR/config.json"
    echo "2. Start: ai-bridge start"
    echo "3. Test: ai-bridge test"
}

main "$@"
