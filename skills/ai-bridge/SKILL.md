---
name: ai-bridge
description: Universal AI-to-AI bridge system. Routes outputs between multiple AI assistants (Kimi, Claude, Gemini, Cursor, ChatGPT, MiniMax) through Slack. Monitors clipboard, files, and triggers handoffs. Runs 24/7 as daemon. Use when user needs to connect multiple AI systems, orchestrate AI workflows, or build autonomous agent networks.
---

# AI Bridge Skill

## Purpose
Bridge multiple AI assistants into a coordinated network. Any AI output can trigger any other AI.

## Architecture
```
User → AI-1 → Slack #ai-war-room → AI-2, AI-3, etc.
         ↑___________________________↓
              (feedback loop)
```

## Components

### 1. Bridge Daemon (`scripts/bridge-daemon.sh`)
- Runs 24/7
- Watches clipboard for AI outputs
- Monitors file drops in `~/ai-outputs/`
- Sends to Slack with source tagging
- Triggers handoffs based on keywords

### 2. Handoff Router (`scripts/router.py`)
- Parses incoming messages
- Routes to target AIs
- Manages conversation threads
- Tracks state

### 3. AI Connectors
Each AI needs a connector script:
- `connectors/kimi.sh` - Webhook/API based
- `connectors/claude.sh` - API based
- `connectors/cursor.sh` - File-based (Cursor can watch files)
- `connectors/gemini.sh` - API based
- `connectors/chatgpt.sh` - Browser automation or API
- `connectors/minimax.sh` - API based

## Installation

```bash
# Run installer
./scripts/install.sh

# Start daemon
ai-bridge start

# Check status
ai-bridge status
```

## Usage

### Manual Routing
Copy any AI output, bridge auto-detects source and sends to Slack.

### Trigger Words (in any AI output)
- `@claude` or `→claude` - Route to Claude
- `@gemini` or `→gemini` - Route to Gemini
- `@cursor` or `→cursor` - Route to Cursor
- `@kimi` or `→kimi` - Route to Kimi
- `@all` or `→all` - Broadcast to all

### Consensus Mode
Type in any AI: `/consensus [question]`
All AIs respond, bridge aggregates.

## State Files
- `~/.ai-bridge/state/queue/` - Pending handoffs
- `~/.ai-bridge/state/threads/` - Conversation threads
- `~/.ai-bridge/state/log` - Activity log

## Configuration
Edit `~/.ai-bridge/config.json`:
```json
{
  "slack_webhook": "YOUR_WEBHOOK",
  "channel": "#ai-war-room",
  "ai_endpoints": {
    "claude": "...",
    "gemini": "...",
    "cursor": "file://...",
    "minimax": "..."
  }
}
```
