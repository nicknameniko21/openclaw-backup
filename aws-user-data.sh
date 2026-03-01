#!/bin/bash
# AWS EC2 User Data - Runs on instance startup
# Installs automation environment

apt-get update
apt-get install -y docker.io docker-compose git jq curl

# Clone repository
cd /opt
git clone https://github.com/nicknameniko21/openclaw-backup.git kimi-claw
cd kimi-claw

# Install Chrome for Selenium
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | tee /etc/apt/sources.list.d/google.list
apt-get update
apt-get install -y google-chrome-stable

# Install Python dependencies
pip3 install selenium requests web3

# Setup cron for automation
cat > /etc/cron.d/kimi-claw <>> /var/log/kimi-claw.log 2>&1
*/5 * * * * root cd /opt/kimi-claw && git pull >> /var/log/kimi-claw.log 2>&1
EOF

chmod 644 /etc/cron.d/kimi-claw

# Start services
service cron restart

echo "Kimi Claw automation ready on $(hostname)" > /var/log/kimi-claw-boot.log
