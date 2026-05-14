# Termux pe Deploy

## Step 1 — Termux Install karo
Play Store ya F-Droid se Termux download karo (F-Droid recommended).

## Step 2 — Repo clone karo
```bash
pkg install git -y
git clone https://github.com/yourusername/telegram-hosting-bot.git
cd telegram-hosting-bot
```

## Step 3 — Setup run karo
```bash
bash scripts/termux_setup.sh
```

## Step 4 — .env file banao
```bash
cp .env.example .env
nano .env
```
Apni values bharo, `Ctrl+X` → `Y` → Enter se save karo.

## Step 5 — Bot start karo
```bash
source .env && python main.py
```

## Background mein chalao (phone band na karo)
```bash
nohup python main.py > bot.log 2>&1 &
```
Logs dekhne ke liye:
```bash
tail -f bot.log
```
