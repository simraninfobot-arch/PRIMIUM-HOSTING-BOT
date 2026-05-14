# VPS pe Deploy (Ubuntu/Debian)

## Step 1 — Repo clone karo
```bash
git clone https://github.com/yourusername/telegram-hosting-bot.git
cd telegram-hosting-bot
```

## Step 2 — Auto setup
```bash
bash scripts/vps_setup.sh
```
Script puchega systemd service banana hai ya nahi — `y` dabo.

## Step 3 — .env file banao
```bash
cp .env.example .env
nano .env
```

## Step 4 — Service start karo
```bash
sudo systemctl start telegram-bot
sudo systemctl status telegram-bot
```

## Useful commands
```bash
# Logs live dekho
sudo journalctl -u telegram-bot -f

# Restart karo
sudo systemctl restart telegram-bot

# Band karo
sudo systemctl stop telegram-bot
```
