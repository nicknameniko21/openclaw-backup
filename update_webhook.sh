#!/bin/bash
# update_webhook.sh - Updates all files with new Slack webhook
# Usage: bash update_webhook.sh "https://hooks.slack.com/services/NEW/URL/HERE"

NEW_WEBHOOK="$1"

if [ -z "$NEW_WEBHOOK" ]; then
    echo "Usage: bash update_webhook.sh 'https://hooks.slack.com/services/NEW/URL'"
    exit 1
fi

echo "Updating all files with new webhook..."

# Old webhook (compromised)
OLD_WEBHOOK="https://hooks.slack.com/services/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"

# Update ai-bridge.sh
sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" /root/.openclaw/workspace/ai-bridge.sh

# Update skills/ai-bridge/scripts/bridge-daemon.sh
sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" /root/.openclaw/workspace/skills/ai-bridge/scripts/bridge-daemon.sh

# Update skills/ai-bridge/scripts/install.sh
sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" /root/.openclaw/workspace/skills/ai-bridge/scripts/install.sh

# Update manuals
sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" /root/.openclaw/workspace/manual/KIMI_CLAW_COMPLETE_MANUAL.md
sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" /root/.openclaw/workspace/manual/VISUAL_MANUAL.md

# Update config files
find /root/.openclaw/workspace -name "config.json" -exec sed -i "s|$OLD_WEBHOOK|$NEW_WEBHOOK|g" {} \;

echo "✅ All files updated with new webhook"
echo ""
echo "Files updated:"
echo "  - ai-bridge.sh"
echo "  - skills/ai-bridge/scripts/bridge-daemon.sh"
echo "  - skills/ai-bridge/scripts/install.sh"
echo "  - manual/KIMI_CLAW_COMPLETE_MANUAL.md"
echo "  - manual/VISUAL_MANUAL.md"
echo "  - All config.json files"
echo ""
echo "Next steps:"
echo "  1. Test the new webhook"
echo "  2. Commit changes to git"
echo "  3. Delete old webhook from Slack"
