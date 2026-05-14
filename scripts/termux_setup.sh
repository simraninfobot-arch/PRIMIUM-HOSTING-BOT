#!/bin/bash
# ============================================
# Termux Setup Script — Telegram Hosting Bot
# Run: bash scripts/termux_setup.sh
# ============================================

set -e

echo "================================================"
echo "  Telegram Hosting Bot — Termux Setup"
echo "================================================"

pkg update -y && pkg upgrade -y
pkg install -y python git curl

pip install --upgrade pip
pip install -r requirements.txt

if [ ! -f ".env" ]; then
    echo ""
    echo "WARNING: .env file nahi mili!"
    echo "Run karo: cp .env.example .env && nano .env"
else
    echo "OK: .env file mil gayi!"
fi

echo ""
echo "Bot start karne ke liye:"
echo "  source .env && python main.py"
echo ""
echo "Background mein chalane ke liye:"
echo "  nohup python main.py > bot.log 2>&1 &"
