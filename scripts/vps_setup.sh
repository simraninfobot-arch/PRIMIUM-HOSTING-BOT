#!/bin/bash
# ============================================
# VPS Setup Script — Telegram Hosting Bot
# Tested: Ubuntu 20.04 / 22.04
# Run: bash scripts/vps_setup.sh
# ============================================

set -e

echo "================================================"
echo "  Telegram Hosting Bot — VPS Setup"
echo "================================================"

# System update
echo "System update ho raha hai..."
sudo apt-get update -y && sudo apt-get upgrade -y

# Python & pip install
echo "Python install ho raha hai..."
sudo apt-get install -y python3 python3-pip python3-venv git curl

# Virtual environment
echo "Virtual environment ban raha hai..."
python3 -m venv venv
source venv/bin/activate

pip install --upgrade pip
pip install -r requirements.txt

# .env file
if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file nahi mili!"
    echo "Run karo: cp .env.example .env && nano .env"
fi

# Systemd service banao
echo ""
echo "Systemd service banana chahte ho? (y/n)"
read -r REPLY
if [[ $REPLY == "y" ]]; then
    WORK_DIR=$(pwd)
    sudo bash -c "cat > /etc/systemd/system/telegram-bot.service << SERVICE
[Unit]
Description=Telegram Hosting Bot
After=network.target

[Service]
Type=simple
User=$USER
WorkingDirectory=$WORK_DIR
EnvironmentFile=$WORK_DIR/.env
ExecStart=$WORK_DIR/venv/bin/python main.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SERVICE"

    sudo systemctl daemon-reload
    sudo systemctl enable telegram-bot
    sudo systemctl start telegram-bot

    echo "Service start ho gayi!"
    echo "Status dekhne ke liye: sudo systemctl status telegram-bot"
    echo "Logs dekhne ke liye: sudo journalctl -u telegram-bot -f"
fi

echo ""
echo "VPS Setup Complete!"
