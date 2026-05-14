#!/bin/bash
# Live logs dekho
tail -f bot.log 2>/dev/null || echo "bot.log file nahi mili. Bot chal raha hai?"
