#!/bin/bash
# Infinite Sub-Agent Spawner
# Spawns parallel workers for any task

TASK="${1:-general work}"
COUNT="${2:-1}"

echo "Spawning $COUNT sub-agent(s) for: $TASK"

for i in $(seq 1 $COUNT); do
    # Create task file for sub-agent
    task_file="/root/.openclaw/workspace/ai-outputs/subagent-task-$(date +%s)-$i.txt"
    cat > "$task_file" << EOF
TASK: $TASK
AGENT_ID: subagent-$i
START_TIME: $(date)
INSTRUCTIONS:
1. Execute the task above
2. Log all actions to memory/
3. Report completion back to ai-outputs/kimi-inbox/
4. If blocked, escalate with @kimi trigger

OUTPUT_FORMAT:
- Timestamp all entries
- Use structured logging
- Save files to workspace
EOF
    
    echo "Created task file: $task_file"
done

echo "Tasks created. Sub-agents will pick up from ai-outputs/"
echo "To actually spawn OpenClaw sub-agents, use:"
echo "  openclaw sessions spawn --task '...' --label 'worker-N'"
