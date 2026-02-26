#!/bin/bash
# inventory.sh - Complete system scanner for agent building
# Creates queryable database of all tools, software, AI parts, docs

set -e

STATE_DIR="$HOME/.ai-centerplus/inventory"
DB_FILE="$STATE_DIR/database.json"
LOG_FILE="$STATE_DIR/inventory.log"

init() {
    mkdir -p "$STATE_DIR"
    touch "$LOG_FILE"
}

log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" | tee -a "$LOG_FILE"
}

# Scan CLI tools
scan_cli_tools() {
    log "Scanning CLI tools..."
    
    local tools=(
        "python3:Python" "node:Node.js" "npm:npm" "yarn:Yarn" "pnpm:pnpm"
        "docker:Docker" "kubectl:kubectl" "helm:Helm"
        "git:Git" "gh:GitHub CLI" "glab:GitLab CLI"
        "aws:AWS CLI" "gcloud:GCloud" "az:Azure CLI"
        "terraform:Terraform" "pulumi:Pulumi" "ansible:Ansible"
        "curl:cURL" "wget:Wget" "jq:jq" "yq:yq"
        "ffmpeg:FFmpeg" "imagemagick:ImageMagick"
        "pandoc:Pandoc" "latex:LaTeX"
        "vim:Vim" "nvim:Neovim" "emacs:Emacs" "code:VS Code"
        "cursor:Cursor" "zed:Zed"
        "tmux:tmux" "screen:GNU Screen"
        "htop:htop" "btop:btop" "glances:Glances"
        "fzf:fzf" "ripgrep:ripgrep" "fd:fd" "bat:bat" "exa:exa/eza"
        "zoxide:zoxide" "starship:Starship"
        "brew:Homebrew" "apt:APT" "yum:YUM" "pacman:Pacman"
        "cargo:Rust/Cargo" "go:Go" "ruby:Ruby" "php:PHP" "java:Java"
        "rustc:Rust" "swift:Swift" "kotlin:Kotlin"
    )
    
    local found_tools=()
    
    for tool_info in "${tools[@]}"; do
        IFS=':' read -r cmd name <<< "$tool_info"
        if command -v "$cmd" >/dev/null 2>&1; then
            local version=$(eval "$cmd --version" 2>/dev/null | head -1 || echo "unknown")
            found_tools+=("{\"name\":\"$name\",\"command\":\"$cmd\",\"version\":\"$version\"}")
        fi
    done
    
    echo "[$(IFS=,; echo "${found_tools[*]}")]"
}

# Scan AI/ML tools
scan_ai_tools() {
    log "Scanning AI/ML tools..."
    
    local ai_tools=(
        "python3 -c 'import torch;print(torch.__version__)':PyTorch"
        "python3 -c 'import tensorflow;print(tensorflow.__version__)':TensorFlow"
        "python3 -c 'import jax;print(jax.__version__)':JAX"
        "python3 -c 'import openai;print(openai.__version__)':OpenAI SDK"
        "python3 -c 'import anthropic;print(anthropic.__version__)':Anthropic SDK"
        "python3 -c 'import langchain;print(langchain.__version__)':LangChain"
        "python3 -c 'import llama_index;print(llama_index.__version__)':LlamaIndex"
        "python3 -c 'import transformers;print(transformers.__version__)':Hugging Face"
        "python3 -c 'import sklearn;print(sklearn.__version__)':scikit-learn"
        "ollama --version:Ollama"
        "lmstudio --version:LM Studio"
        "open-webui --version:Open WebUI"
    )
    
    local found_ai=()
    
    for tool_info in "${ai_tools[@]}"; do
        IFS=':' read -r cmd name <<< "$tool_info"
        if eval "$cmd" >/dev/null 2>&1; then
            local version=$(eval "$cmd" 2>/dev/null | head -1 || echo "installed")
            found_ai+=("{\"name\":\"$name\",\"version\":\"$version\"}")
        fi
    done
    
    echo "[$(IFS=,; echo "${found_ai[*]}")]"
}

# Scan API keys (presence only, safe)
scan_api_keys() {
    log "Scanning API keys..."
    
    local keys=(
        "OPENAI_API_KEY:OpenAI"
        "ANTHROPIC_API_KEY:Anthropic"
        "GOOGLE_API_KEY:Google/Gemini"
        "AZURE_OPENAI_KEY:Azure OpenAI"
        "COHERE_API_KEY:Cohere"
        "HUGGINGFACE_TOKEN:Hugging Face"
        "REPLICATE_API_TOKEN:Replicate"
        "ELEVENLABS_API_KEY:ElevenLabs"
        "PINECONE_API_KEY:Pinecone"
        "WEAVIATE_API_KEY:Weaviate"
        "QDRANT_API_KEY:Qdrant"
        "MILVUS_TOKEN:Milvus"
        "CHROMA_TOKEN:Chroma"
        "AWS_ACCESS_KEY_ID:AWS"
        "GCP_SERVICE_ACCOUNT_KEY:GCP"
        "AZURE_CLIENT_SECRET:Azure"
        "GITHUB_TOKEN:GitHub"
        "GITLAB_TOKEN:GitLab"
        "SLACK_BOT_TOKEN:Slack"
        "DISCORD_BOT_TOKEN:Discord"
        "TELEGRAM_BOT_TOKEN:Telegram"
        "NOTION_TOKEN:Notion"
        "AIRTABLE_API_KEY:Airtable"
        "TAVILY_API_KEY:Tavily"
        "SERPER_API_KEY:Serper"
        "BRAVE_API_KEY:Brave Search"
        "FIRECRAWL_API_KEY:Firecrawl"
        "APIFY_API_TOKEN:Apify"
    )
    
    local found_keys=()
    
    for key_info in "${keys[@]}"; do
        IFS=':' read -r var name <<< "$key_info"
        if [ -n "${!var:-}" ] || grep -r "$var" ~/.bashrc ~/.zshrc ~/.profile ~/.env 2>/dev/null | grep -q "export"; then
            found_keys+=("{\"service\":\"$name\",\"key\":\"$var\",\"status\":\"configured\"}")
        fi
    done
    
    # Check common env files
    for env_file in ~/.env ~/.env.local .env; do
        if [ -f "$env_file" ]; then
            while IFS= read -r line; do
                if [[ "$line" =~ ^([A-Z_]+_API_KEY|OPENAI_API_KEY|ANTHROPIC_API_KEY)= ]]; then
                    local key_name="${BASH_REMATCH[1]}"
                    if ! echo "${found_keys[@]}" | grep -q "$key_name"; then
                        found_keys+=("{\"service\":\"unknown\",\"key\":\"$key_name\",\"status\":\"configured\"}")
                    fi
                fi
            done < "$env_file"
        fi
    done
    
    echo "[$(IFS=,; echo "${found_keys[*]}")]"
}

# Scan Git repositories
scan_repos() {
    log "Scanning Git repositories..."
    
    local repos=()
    local search_dirs=("$HOME" "$HOME/projects" "$HOME/code" "$HOME/dev" "$HOME/workspace")
    
    for dir in "${search_dirs[@]}"; do
        if [ -d "$dir" ]; then
            while IFS= read -r gitdir; do
                local repo_path=$(dirname "$gitdir")
                local repo_name=$(basename "$repo_path")
                local remote=$(cd "$repo_path" && git remote get-url origin 2>/dev/null || echo "no remote")
                local branch=$(cd "$repo_path" && git branch --show-current 2>/dev/null || echo "detached")
                
                repos+=("{\"name\":\"$repo_name\",\"path\":\"$repo_path\",\"remote\":\"$remote\",\"branch\":\"$branch\"}")
            done < <(find "$dir" -maxdepth 3 -name ".git" -type d 2>/dev/null | head -100)
        fi
    done
    
    echo "[$(IFS=,; echo "${repos[*]}")]"
}

# Scan documentation
scan_docs() {
    log "Scanning documentation..."
    
    local docs=()
    local doc_dirs=("$HOME/Documents" "$HOME/Notes" "$HOME/notes" "$HOME/Dropbox" "$HOME/Google Drive")
    
    for dir in "${doc_dirs[@]}"; do
        if [ -d "$dir" ]; then
            while IFS= read -r file; do
                local filename=$(basename "$file")
                local category="other"
                
                case "$filename" in
                    *.md) category="markdown" ;;
                    *.txt) category="text" ;;
                    *.pdf) category="pdf" ;;
                    *.doc|*.docx) category="word" ;;
                    *.xls|*.xlsx) category="excel" ;;
                    *.ppt|*.pptx) category="powerpoint" ;;
                esac
                
                docs+=("{\"name\":\"$filename\",\"path\":\"$file\",\"type\":\"$category\"}")
            done < <(find "$dir" -maxdepth 3 \( -name "*.md" -o -name "*.txt" -o -name "*.pdf" -o -name "*.docx" \) 2>/dev/null | head -200)
        fi
    done
    
    echo "[$(IFS=,; echo "${docs[*]}")]"
}

# Scan package managers
scan_packages() {
    log "Scanning package managers..."
    
    local packages="{}"
    
    # Homebrew
    if command -v brew >/dev/null 2>&1; then
        local brew_count=$(brew list 2>/dev/null | wc -l | tr -d ' ')
        packages=$(echo "$packages" | jq --arg count "$brew_count" '. + {homebrew: {count: $count}}')
    fi
    
    # npm
    if command -v npm >/dev/null 2>&1; then
        local npm_count=$(npm list -g --depth=0 2>/dev/null | wc -l | tr -d ' ')
        packages=$(echo "$packages" | jq --arg count "$npm_count" '. + {npm: {count: $count}}')
    fi
    
    # pip
    if command -v pip3 >/dev/null 2>&1; then
        local pip_count=$(pip3 list 2>/dev/null | wc -l | tr -d ' ')
        packages=$(echo "$packages" | jq --arg count "$pip_count" '. + {pip: {count: $count}}')
    fi
    
    # Cargo
    if command -v cargo >/dev/null 2>&1; then
        local cargo_count=$(cargo install --list 2>/dev/null | wc -l | tr -d ' ')
        packages=$(echo "$packages" | jq --arg count "$cargo_count" '. + {cargo: {count: $count}}')
    fi
    
    echo "$packages"
}

# Build full database
build_database() {
    log "Building inventory database..."
    
    local cli_tools=$(scan_cli_tools)
    local ai_tools=$(scan_ai_tools)
    local api_keys=$(scan_api_keys)
    local repos=$(scan_repos)
    local docs=$(scan_docs)
    local packages=$(scan_packages)
    
    local db=$(jq -n \
        --arg timestamp "$(date -u +%Y-%m-%dT%H:%M:%SZ)" \
        --argjson cli "$cli_tools" \
        --argjson ai "$ai_tools" \
        --argjson keys "$api_keys" \
        --argjson repos "$repos" \
        --argjson docs "$docs" \
        --argjson pkgs "$packages" \
        '{
            metadata: {
                generated_at: $timestamp,
                version: "1.0"
            },
            cli_tools: $cli,
            ai_tools: $ai,
            api_keys: $keys,
            repositories: $repos,
            documentation: $docs,
            packages: $pkgs
        }')
    
    echo "$db" > "$DB_FILE"
    log "Database saved to $DB_FILE"
}

# Query functions
query_tools() {
    local search="${1:-}"
    if [ -f "$DB_FILE" ]; then
        if [ -n "$search" ]; then
            jq --arg s "$search" '.cli_tools[] | select(.name | test($s; "i"))' "$DB_FILE"
        else
            jq '.cli_tools[]' "$DB_FILE"
        fi
    else
        echo "Database not found. Run: inventory scan"
    fi
}

query_ai() {
    if [ -f "$DB_FILE" ]; then
        jq '.ai_tools[]' "$DB_FILE"
    else
        echo "Database not found. Run: inventory scan"
    fi
}

query_keys() {
    if [ -f "$DB_FILE" ]; then
        jq '.api_keys[]' "$DB_FILE"
    else
        echo "Database not found. Run: inventory scan"
    fi
}

query_repos() {
    if [ -f "$DB_FILE" ]; then
        jq '.repositories[]' "$DB_FILE"
    else
        echo "Database not found. Run: inventory scan"
    fi
}

query_docs() {
    local search="${1:-}"
    if [ -f "$DB_FILE" ]; then
        if [ -n "$search" ]; then
            jq --arg s "$search" '.documentation[] | select(.name | test($s; "i"))' "$DB_FILE"
        else
            jq '.documentation[]' "$DB_FILE"
        fi
    else
        echo "Database not found. Run: inventory scan"
    fi
}

# Suggest workflows based on available tools
suggest_workflows() {
    if [ ! -f "$DB_FILE" ]; then
        echo "Database not found. Run: inventory scan"
        return
    fi
    
    echo "=== SUGGESTED WORKFLOWS ==="
    echo
    
    # Check for AI tools
    if jq -e '.ai_tools | length > 0' "$DB_FILE" >/dev/null 2>&1; then
        echo "AI Development:"
        echo "  - Local LLM inference with Ollama/LM Studio"
        echo "  - RAG pipeline with LangChain + vector DB"
        echo "  - Fine-tuning with Hugging Face"
        echo
    fi
    
    # Check for cloud tools
    if jq -e '.cli_tools[] | select(.name | contains("AWS") or contains("Azure") or contains("GCloud"))' "$DB_FILE" >/dev/null 2>&1; then
        echo "Cloud Deployment:"
        echo "  - Serverless functions"
        echo "  - Container orchestration"
        echo "  - Infrastructure as Code"
        echo
    fi
    
    # Check for Docker
    if jq -e '.cli_tools[] | select(.command == "docker")' "$DB_FILE" >/dev/null 2>&1; then
        echo "Containerization:"
        echo "  - Docker Compose stacks"
        echo "  - Kubernetes deployments"
        echo "  - CI/CD pipelines"
        echo
    fi
}

# Main commands
case "${1:-scan}" in
    scan|build)
        init
        build_database
        ;;
    tools)
        query_tools "$2"
        ;;
    ai)
        query_ai
        ;;
    keys)
        query_keys
        ;;
    repos)
        query_repos
        ;;
    docs)
        query_docs "$2"
        ;;
    search)
        query_tools "$2"
        query_docs "$2"
        ;;
    workflows|suggest)
        suggest_workflows
        ;;
    status)
        if [ -f "$DB_FILE" ]; then
            echo "Database: $DB_FILE"
            echo "Generated: $(jq -r '.metadata.generated_at' "$DB_FILE")"
            echo "CLI tools: $(jq '.cli_tools | length' "$DB_FILE")"
            echo "AI tools: $(jq '.ai_tools | length' "$DB_FILE")"
            echo "API keys: $(jq '.api_keys | length' "$DB_FILE")"
            echo "Repositories: $(jq '.repositories | length' "$DB_FILE")"
            echo "Documents: $(jq '.documentation | length' "$DB_FILE")"
        else
            echo "No database found. Run: inventory scan"
        fi
        ;;
    *)
        echo "Usage: inventory {scan|tools|ai|keys|repos|docs|search|workflows|status}"
        echo
        echo "Commands:"
        echo "  scan       - Build/rebuild the database"
        echo "  tools      - List CLI tools (optional: search term)"
        echo "  ai         - List AI/ML tools"
        echo "  keys       - List configured API keys"
        echo "  repos      - List Git repositories"
        echo "  docs       - List documentation (optional: search term)"
        echo "  search     - Search across tools and docs"
        echo "  workflows  - Suggest workflows based on your tools"
        echo "  status     - Show database summary"
        exit 1
        ;;
esac
