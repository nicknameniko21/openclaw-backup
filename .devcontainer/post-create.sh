#!/bin/bash
# Post-create setup for Codespace
# Runs once when Codespace is created

echo "Setting up Kimi Claw Automation Environment..."

# Install Python dependencies
pip install --user selenium requests web3 python-dotenv

# Install Chrome for Selenium
wget -q -O - https://dl-ssl.google.com/linux/linux_signing_key.pub | sudo apt-key add -
echo "deb http://dl.google.com/linux/chrome/deb/ stable main" | sudo tee /etc/apt/sources.list.d/google.list
sudo apt-get update
sudo apt-get install -y google-chrome-stable

# Install ChromeDriver
CHROME_VERSION=$(google-chrome --version | awk '{print $3}' | cut -d. -f1)
wget -q "https://chromedriver.storage.googleapis.com/LATEST_RELEASE_$CHROME_VERSION" -O /tmp/chromedriver_version
DRIVER_VERSION=$(cat /tmp/chromedriver_version)
wget -q "https://chromedriver.storage.googleapis.com/$DRIVER_VERSION/chromedriver_linux64.zip" -O /tmp/chromedriver.zip
unzip -q /tmp/chromedriver.zip -d /tmp
sudo mv /tmp/chromedriver /usr/local/bin/
sudo chmod +x /usr/local/bin/chromedriver

# Setup workspace
git config --global user.name "Kimi Claw"
git config --global user.email "kimi-claw@automation.local"

# Create necessary directories
mkdir -p ~/.openclaw
mkdir -p ~/ai-outputs
mkdir -p ~/.bankr

echo "Setup complete!"
