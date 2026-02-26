# AI Bridge - Quick Reference

## Installation
```bash
cd ~/.openclaw/workspace/skills/ai-bridge/scripts
./install.sh
```

## Commands
| Command | Description |
|---------|-------------|
| `ai-bridge start` | Start 24/7 daemon |
| `ai-bridge stop` | Stop daemon |
| `ai-bridge status` | Check if running |
| `ai-bridge log` | Tail logs |
| `ai-bridge test` | Test Slack connection |
| `ai-bridge config` | Show config |

## Trigger Words (in any AI output)
- `@claude` or `→claude` - Route to Claude
- `@gemini` or `→gemini` - Route to Gemini
- `@cursor` or `→cursor` - Route to Cursor
- `@kimi` or `→kimi` - Route to Kimi
- `@chatgpt` or `→chatgpt` - Route to ChatGPT
- `@minimax` or `→minimax` - Route to MiniMax
- `@all` - Broadcast to all
- `/consensus [question]` - Request all AIs respond

## How It Works
1. **Clipboard Watcher** - Detects when you copy AI output
2. **File Watcher** - Monitors `~/ai-outputs/` for file drops
3. **Slack Bridge** - Sends all outputs to #ai-war-room
4. **Trigger Parser** - Checks for handoff keywords
5. **Queue Processor** - Routes to target AIs

## File Structure
```
~/.ai-bridge/
├── config.json          # Main config
├── bridge-daemon.sh     # Daemon script
├── state/
│   ├── bridge.log       # Activity log
│   ├── daemon.pid       # Process ID
│   ├── queue/           # Pending handoffs
│   ├── threads/         # Conversation threads
│   └── processed/       # Processed files
└── connectors/          # AI-specific connectors
```

## Configuring AI Endpoints

Edit `~/.ai-bridge/config.json`:

```json
{
  "ai_endpoints": {
    "claude": "https://your-claude-webhook...",
    "gemini": "https://your-gemini-webhook...",
    "cursor": "file:///tmp/cursor-bridge",
    "kimi": "",
    "chatgpt": "",
    "minimax": ""
  }
}
```

### Endpoint Types
- **HTTP/HTTPS** - POST webhook
- **file://** - Write to directory (for local apps like Cursor)

## Cursor Integration
Cursor can watch a directory for incoming files:

1. Set endpoint: `"cursor": "file:///tmp/cursor-bridge"`
2. In Cursor, set up file watcher or use extension
3. Bridge writes files: `/tmp/cursor-bridge/bridge-inbox-[timestamp].txt`

## Auto-Start

### macOS
```bash
launchctl load ~/Library/LaunchAgents/com.ai-bridge.daemon.plist
```

### Linux
```bash
sudo systemctl enable ai-bridge
sudo systemctl start ai-bridge
```
