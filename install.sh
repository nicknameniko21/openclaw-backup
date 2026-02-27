#!/bin/bash
# One-Click Installer for Kimi Claw
# Deploys complete AI orchestration system

set -e

echo "🦾 Kimi Claw One-Click Installer"
echo "================================"
echo ""

# Check requirements
command -v git >/dev/null 2>&1 || { echo "❌ Git required. Install: apt-get install git"; exit 1; }
command -v python3 >/dev/null 2>&1 || { echo "❌ Python3 required. Install: apt-get install python3"; exit 1; }

# Configuration
INSTALL_DIR="${HOME}/kimi-claw"
REPO_URL="https://github.com/nicknameniko21/openclaw-backup.git"

echo "📁 Installing to: $INSTALL_DIR"
echo ""

# Clone repository
if [ -d "$INSTALL_DIR" ]; then
    echo "🔄 Updating existing installation..."
    cd "$INSTALL_DIR"
    git pull origin main
else
    echo "📥 Cloning repository..."
    git clone "$REPO_URL" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

echo ""
echo "🔧 Setting up components..."

# Create virtual environment
python3 -m venv venv 2>/dev/null || true
source venv/bin/activate

# Install Python dependencies
pip install -q fastapi uvicorn pydantic python-jose requests 2>/dev/null || true

echo ""
echo "🚀 Starting services..."

# Start API Proxy Service
cd monetization
nohup python3 api_proxy.py > /tmp/api_proxy.log 2>&1 &
echo "✅ API Proxy running on port 8082"

# Start AI Identity Pro
cd ../ai-identity-pro/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8000 > /tmp/ai_identity.log 2>&1 &
echo "✅ AI Identity Pro API on port 8000"

cd ../frontend/public
nohup python3 -m http.server 3000 > /tmp/ai_identity_web.log 2>&1 &
echo "✅ AI Identity Pro Web on port 3000"

# Start Meetily Pro
cd ../../meetily-pro/backend
nohup python3 -m uvicorn main:app --host 0.0.0.0 --port 8001 > /tmp/meetily.log 2>&1 &
echo "✅ Meetily Pro API on port 8001"

cd ../frontend/public
nohup python3 -m http.server 3001 > /tmp/meetily_web.log 2>&1 &
echo "✅ Meetily Pro Web on port 3001"

echo ""
echo "================================"
echo "🎉 Installation Complete!"
echo "================================"
echo ""
echo "Services running:"
echo "  • API Proxy:      http://localhost:8082"
echo "  • AI Identity:    http://localhost:3000"
echo "  • AI Identity API:http://localhost:8000"
echo "  • Meetily Pro:    http://localhost:3001"
echo "  • Meetily API:    http://localhost:8001"
echo ""
echo "Logs: /tmp/*.log"
echo ""
echo "To stop all services: pkill -f 'uvicorn\|http.server'"
echo ""
