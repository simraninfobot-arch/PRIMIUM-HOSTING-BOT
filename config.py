import os

# --- [CONFIGURATION] ---
# ✅ Saari values environment variables se aati hain
# ❌ Yahan koi token ya ID hardcode mat karo

# 🔑 Bot Token
TOKEN = os.environ.get('BOT_TOKEN', '')

# 👤 Admin IDs
ADMIN_IDS = [
    int(os.environ.get('ADMIN_ID_1', '0')),
    int(os.environ.get('ADMIN_ID_2', '0')),
    int(os.environ.get('ADMIN_ID_3', '0')),
    int(os.environ.get('ADMIN_ID_4', '0')),
    int(os.environ.get('ADMIN_ID_5', '0')),
    int(os.environ.get('OWNER_ID', '0')),
]
ADMIN_IDS = [aid for aid in ADMIN_IDS if aid != 0]

PRIMARY_ADMIN_ID = ADMIN_IDS[0] if ADMIN_IDS else 0

# 👑 Owner
OWNER_ID = int(os.environ.get('OWNER_ID', '0'))

# 👤 Admin Display Info
ADMIN_USERNAME = os.environ.get('ADMIN_USERNAME', 'your_username')
ADMIN_DISPLAY_NAME = os.environ.get('ADMIN_DISPLAY_NAME', '💞 Your Name 💞')

# 👥 Group ID
GROUP_ID = int(os.environ.get('GROUP_ID', '0'))

# 🐙 GitHub Integration
GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
GITHUB_REPO = os.environ.get('GITHUB_REPO', '')

# 📢 Channel Mandatory Settings
REQUIRED_CHANNEL = os.environ.get('REQUIRED_CHANNEL', 'https://t.me/yourchannel')
REQUIRED_CHANNEL_ID = int(os.environ.get('REQUIRED_CHANNEL_ID', '0'))

# 🌐 Server
BASE_DIR = os.path.join(os.getcwd(), "hosted_projects")
PORT = int(os.environ.get('PORT', 8080))
WEBHOOK_URL = os.environ.get('WEBHOOK_URL', '')
