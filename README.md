# 🤖 Telegram Hosting Bot — Premium v1

> **Deploy karo apna Telegram bot bilkul free mein — Termux, VPS, Docker, Koyeb, Railway, Render sab pe!**

[![Python](https://img.shields.io/badge/Python-3.11+-blue?logo=python)](https://python.org)
[![Telegram](https://img.shields.io/badge/Telegram%20Bot%20API-20.7-blue?logo=telegram)](https://python-telegram-bot.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue?logo=docker)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

---

## 🌟 Features

| Feature | Description |
|---------|-------------|
| 🗳️ Upload Manager | `.zip` file bhejo, bot host ho jayega |
| 📮 File Manager | Projects run/stop karo |
| 📺 Live Logs | Real-time terminal output Telegram mein |
| 🛡️ Auto Recovery | Crash hone pe automatically restart |
| 🔄 Auto Restart | Process band ho to khud se chalu |
| 🔒 System Lock | Admin bot ko lock/unlock kar sakta hai |
| 🏩 System Health | CPU, RAM, Disk stats |
| 📢 Channel Gate | Channel join karna zaroori |

---

## 📁 Project Structure

```
telegram-hosting-bot/
├── main.py                    ← Bot entry point
├── config.py                  ← Environment variables config
├── requirements.txt           ← Python dependencies
├── .env.example               ← Environment template (copy karke .env banao)
├── .gitignore
│
├── 🐳 Docker
│   ├── Dockerfile
│   └── docker-compose.yml
│
├── ☁️ Cloud Deploy
│   ├── Procfile               ← Heroku / Railway
│   ├── render.yaml            ← Render
│   ├── railway.toml           ← Railway
│   ├── nixpacks.toml          ← Railway (Nixpacks)
│   ├── runtime.txt            ← Python version
│   └── app.json               ← One-click deploy config
│
├── 📜 scripts/
│   ├── termux_setup.sh        ← Termux auto install
│   ├── vps_setup.sh           ← VPS auto install (Ubuntu)
│   ├── start.sh               ← Bot start
│   ├── stop.sh                ← Bot stop
│   └── logs.sh                ← Live logs
│
├── 📚 docs/
│   ├── TERMUX.md              ← Termux guide
│   ├── VPS.md                 ← VPS guide
│   └── DOCKER.md              ← Docker guide
│
├── 📋 CHANGELOG.md
├── 🤝 CONTRIBUTING.md
├── ⚖️ LICENSE
│
└── modules/
    ├── log_streamer.py
    ├── loading.py
    ├── recovery.py
    ├── health.py
    └── web_server.py
```

---

## ⚡ Quick Start

### 📱 Termux (Android)
```bash
git clone https://github.com/yourusername/telegram-hosting-bot.git
cd telegram-hosting-bot
bash scripts/termux_setup.sh
cp .env.example .env && nano .env
source .env && python main.py
```
👉 Full guide: [docs/TERMUX.md](docs/TERMUX.md)

### 🖥️ VPS (Ubuntu/Debian)
```bash
git clone https://github.com/yourusername/telegram-hosting-bot.git
cd telegram-hosting-bot
bash scripts/vps_setup.sh
cp .env.example .env && nano .env
```
👉 Full guide: [docs/VPS.md](docs/VPS.md)

### 🐳 Docker
```bash
git clone https://github.com/yourusername/telegram-hosting-bot.git
cd telegram-hosting-bot
cp .env.example .env && nano .env
docker-compose up -d
```
👉 Full guide: [docs/DOCKER.md](docs/DOCKER.md)

---

## 🚀 Cloud Deploy (Free)

### ▶️ Koyeb (RECOMMENDED)
1. Repo fork karo
2. [koyeb.com](https://koyeb.com) → Create App → GitHub → apna repo
3. Environment variables add karo (`.env.example` dekho)
4. Deploy ✅

### ▶️ Railway
1. Repo fork karo
2. [railway.app](https://railway.app) → New Project → GitHub repo
3. Variables tab mein `.env.example` values add karo
4. Auto deploy ✅

### ▶️ Render
1. Repo fork karo
2. [render.com](https://render.com) → New Web Service → GitHub
3. Build: `pip install -r requirements.txt` | Start: `python main.py`
4. Environment variables add karo ✅

---

## ⚙️ Environment Variables

`.env.example` file copy karo:
```bash
cp .env.example .env
```

| Variable | Description | Required |
|----------|-------------|----------|
| `BOT_TOKEN` | @BotFather se milega | ✅ |
| `ADMIN_ID_1` | Apna Telegram User ID | ✅ |
| `OWNER_ID` | Owner Telegram User ID | ✅ |
| `GROUP_ID` | Group ID (`-100...`) | Optional |
| `GITHUB_TOKEN` | GitHub Personal Access Token | Optional |
| `GITHUB_REPO` | `username/reponame` format | Optional |
| `REQUIRED_CHANNEL` | Channel link | Optional |
| `REQUIRED_CHANNEL_ID` | Channel ID (`-100...`) | Optional |
| `PORT` | Server port (default: `8080`) | Optional |
| `WEBHOOK_URL` | Webhook URL (blank = polling) | Optional |

---

## ❓ FAQ

**Q: Bot token kahan se milega?**
> [@BotFather](https://t.me/BotFather) → `/newbot`

**Q: Apna Telegram ID kaise pata karein?**
> [@userinfobot](https://t.me/userinfobot) ko `/start` bhejo

**Q: Channel ID kaise pata karein?**
> Channel ka message [@userinfobot](https://t.me/userinfobot) ko forward karo

**Q: Termux mein phone band ho gaya, bot bhi band hua?**
> `nohup python main.py > bot.log 2>&1 &` use karo background mein chalne ke liye

---

## 👤 Owner

Made with 💙 by **aalyanmods**

[![Telegram](https://img.shields.io/badge/Telegram-aalyanmods-blue?logo=telegram)](https://t.me/aalyanmods)

> ⭐ Agar pasand aaya to Star dena mat bhoolo!
