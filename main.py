import os
import zipfile
import subprocess
import sys
import shutil
import asyncio
import logging
import signal
from threading import Thread

from telegram import ReplyKeyboardMarkup, KeyboardButton, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes

from config import (
    TOKEN, ADMIN_IDS, PRIMARY_ADMIN_ID, ADMIN_USERNAME, ADMIN_DISPLAY_NAME,
    REQUIRED_CHANNEL, REQUIRED_CHANNEL_ID, BASE_DIR, PORT
)
from modules.log_streamer import LogStreamer, user_log_sessions
from modules.loading import Loading, animate
from modules.health import get_system_health
from modules.recovery import BotRecovery
from modules.web_server import run_web

# ---- LOGGING SETUP ----
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# ---- CREATE DIRS ----
if not os.path.exists(BASE_DIR):
    os.makedirs(BASE_DIR)

# ---- GLOBAL STATE ----
running_processes = {}
bot_locked = False
auto_restart_mode = False
user_upload_state = {}
project_owners = {}
recovery_enabled = True
live_logs_enabled = True

# ---- INIT SYSTEMS ----
log_streamer = LogStreamer()
recovery_system = BotRecovery()


# ---- AUTO PACKAGE INSTALLER ----
def auto_install_packages():
    required_packages = ['flask', 'python-telegram-bot', 'psutil', 'aiohttp']
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            logger.info(f"📦 Installing {package}...")
            try:
                subprocess.check_call([sys.executable, "-m", "pip", "install", package, "--quiet"])
                logger.info(f"✅ {package} installed")
            except Exception as e:
                logger.error(f"❌ Failed to install {package}: {e}")

auto_install_packages()


# ---- HELPERS ----
def is_admin(user_id):
    return user_id in ADMIN_IDS


async def check_channel_membership(user_id: int, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if not REQUIRED_CHANNEL_ID:
        return True
    if is_admin(user_id):
        return True
    try:
        member = await context.bot.get_chat_member(chat_id=REQUIRED_CHANNEL_ID, user_id=user_id)
        return member.status not in ['left', 'kicked', 'banned']
    except Exception as e:
        logger.error(f"Membership check error: {e}")
        return False


async def require_channel_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await check_channel_membership(user_id, context):
        keyboard = [
            [InlineKeyboardButton("📢 Join Channel", url=REQUIRED_CHANNEL)],
            [InlineKeyboardButton("✅ I have joined", callback_data="check_join")]
        ]
        msg = "⚠️ **You must join our official channel to use this bot!**\n\n1. Click below to join.\n2. After joining, click 'I have joined'."
        if update.message:
            await update.message.reply_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        elif getattr(update, 'callback_query', None):
            await update.callback_query.edit_message_text(msg, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode='Markdown')
        return False
    return True


def get_main_keyboard(user_id):
    lock_status = "🔓 UNLOCK SYSTEM" if bot_locked else "🔒 LOCK SYSTEM"
    restart_status = "🔄 AUTO RESTART: OFF" if auto_restart_mode else "🔄 AUTO RESTART: ON"
    recovery_status = "🛡️ RECOVERY: OFF" if recovery_enabled else "🛡️ RECOVERY: ON"
    logs_status = "📺 LIVE LOGS: OFF" if live_logs_enabled else "📺 LIVE LOGS: ON"

    if is_admin(user_id):
        layout = [
            [KeyboardButton("🗳️ UPLOAD MANAGER"), KeyboardButton("📮 FILE MANAGER")],
            [KeyboardButton("🗑️ DELETE MANAGER"), KeyboardButton("🏩 SYSTEM HEALTH")],
            [KeyboardButton("🌎 SERVER INFO"), KeyboardButton("📠 CONTACT ADMIN")],
            [KeyboardButton(lock_status), KeyboardButton(restart_status)],
            [KeyboardButton(recovery_status), KeyboardButton("🎬 PROJECT FILE")],
            [KeyboardButton(logs_status)]
        ]
    else:
        layout = [
            [KeyboardButton("🗳️ UPLOAD MANAGER"), KeyboardButton("📮 FILE MANAGER")],
            [KeyboardButton("🗑️ DELETE MANAGER"), KeyboardButton("🏩 SYSTEM HEALTH")],
            [KeyboardButton("🌎 SERVER INFO"), KeyboardButton("📠 CONTACT ADMIN")],
            [KeyboardButton(logs_status)]
        ]
    return ReplyKeyboardMarkup(layout, resize_keyboard=True)


# ---- LIVE LOGS VIEWER TASK ----
async def log_viewer_task(context: ContextTypes.DEFAULT_TYPE):
    """Background task that updates user log messages"""
    logger.info("📝 Log viewer task started")
    while True:
        try:
            if not live_logs_enabled:
                await asyncio.sleep(2)
                continue

            import time as _time
            current_time = _time.time()

            for user_id, session in list(user_log_sessions.items()):
                if not session["active"]:
                    continue
                if current_time - session["last_update"] < 2:
                    continue

                logs = session["buffer"][-20:]
                session["buffer"] = []

                if not logs and not session.get("has_content"):
                    continue

                log_text = "\n".join(logs) if logs else "⏳ Waiting for logs..."
                terminal_text = (
                    f"📺 **LIVE CONSOLE - {session['project']}**\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"```\n{log_text[-3500:]}\n```\n"
                    f"━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🟢 ONLINE | 🔄 AUTO-UPDATE: 2s"
                )

                try:
                    await context.bot.edit_message_text(
                        chat_id=session["chat_id"],
                        message_id=session["message_id"],
                        text=terminal_text,
                        parse_mode='Markdown'
                    )
                    session["last_update"] = current_time
                    session["has_content"] = True
                except Exception as e:
                    if "message is not modified" not in str(e).lower():
                        if "message to edit not found" in str(e).lower():
                            session["active"] = False

            await asyncio.sleep(0.5)

        except Exception as e:
            logger.error(f"Log viewer task error: {e}")
            await asyncio.sleep(2)


# ---- PROCESS MONITOR ----
async def monitor_process(p_name, folder):
    """Auto-restart monitor"""
    while auto_restart_mode and p_name in running_processes:
        proc = running_processes.get(p_name)
        if proc and proc.poll() is not None:
            await asyncio.sleep(2)
            main_file = os.path.join(folder, "main.py")
            if os.path.exists(main_file):
                new_proc = subprocess.Popen(
                    [sys.executable, "-u", main_file],
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                running_processes[p_name] = new_proc
                if live_logs_enabled:
                    log_streamer.stop_stream(p_name)
                    log_streamer.start_stream(p_name, new_proc)
                logger.info(f"Auto-restarted {p_name}")
        await asyncio.sleep(5)


# ---- HANDLERS ----
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_channel_join(update, context):
        return
    if bot_locked and not is_admin(user_id):
        await update.message.reply_text("🔒 **System is currently locked by admin**", parse_mode='Markdown')
        return
    msg = (
        "🌍 **LAM PREMIUM HOSTING V1** 🌸\n"
        "━━━━━━━━━━━━━━━━━━━━━\n"
        "💙 **WELCOME TO THE ELITE PANEL**\n"
        "🔮 **Welcome! This is the most powerful premium server.**\n\n"
        f"🇮🇳 **OWNER:** `{ADMIN_USERNAME}`\n"
        f"📢 **CHANNEL:** {'Not Set' if not REQUIRED_CHANNEL else REQUIRED_CHANNEL}\n"
        "━━━━━━━━━━━━━━━━━━━━━"
    )
    await update.message.reply_text(msg, reply_markup=get_main_keyboard(user_id), parse_mode='Markdown')


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text
    global bot_locked, auto_restart_mode, recovery_enabled, live_logs_enabled

    if not await require_channel_join(update, context):
        return
    if bot_locked and not is_admin(user_id):
        await update.message.reply_text("🔒 **System is currently locked.**", parse_mode='Markdown')
        return

    # Live logs toggle
    if "📺 LIVE LOGS:" in text:
        if "ON" in text:
            live_logs_enabled = True
            await animate(update, context, Loading.logs_on(), delay=0.5, final_text="📺 **LIVE LOGS: ENABLED**")
        else:
            live_logs_enabled = False
            for uid in list(user_log_sessions.keys()):
                log_streamer.unsubscribe(uid)
            await animate(update, context, Loading.logs_off(), delay=0.5, final_text="❌ **LIVE LOGS: DISABLED**")
        await update.message.reply_text("Menu updated!", reply_markup=get_main_keyboard(user_id))
        return

    # Project naming after upload
    if user_id in user_upload_state and "path" in user_upload_state[user_id]:
        p_name = text.replace(" ", "_").replace("/", "_")
        state = user_upload_state[user_id]
        extract_path = os.path.join(BASE_DIR, p_name)

        try:
            msg = await animate(update, context, Loading.executing(), delay=0.4)
            os.makedirs(extract_path, exist_ok=True)
            with zipfile.ZipFile(state["path"], 'r') as zip_ref:
                zip_ref.extractall(extract_path)

            main_py = os.path.join(extract_path, "main.py")
            req_txt = os.path.join(extract_path, "requirements.txt")

            if not os.path.exists(main_py):
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=msg.message_id,
                    text="❌ **ERROR: main.py not found in zip!**",
                    parse_mode='Markdown'
                )
                shutil.rmtree(extract_path)
                return

            if os.path.exists(req_txt):
                for frame in Loading.installing():
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=msg.message_id,
                        text=frame
                    )
                    await asyncio.sleep(1.0)
                try:
                    subprocess.run(
                        [sys.executable, "-m", "pip", "install", "-r", req_txt],
                        check=True, capture_output=True, text=True, cwd=extract_path
                    )
                except subprocess.CalledProcessError as e:
                    logger.error(f"Requirements install failed: {e}")
                    await context.bot.edit_message_text(
                        chat_id=update.effective_chat.id,
                        message_id=msg.message_id,
                        text="⚠️ **WARNING: Some requirements failed to install**",
                        parse_mode='Markdown'
                    )
                    await asyncio.sleep(1)

            project_owners[p_name] = {
                "u_id": user_id,
                "u_name": state["u_name"],
                "u_username": update.effective_user.username or "no_username",
                "zip": state["path"],
                "original_name": state["original_name"],
                "path": extract_path
            }
            del user_upload_state[user_id]

            final_text = (
                f"✅ **PROJECT `{p_name}` SAVED!**\n"
                f"━━━━━━━━━━━━━━━━━━━━━\n"
                f"🚀 **Go to '📮 FILE MANAGER' and run it.**\n"
                f"━━━━━━━━━━━━━━━━━━━━━"
            )
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=final_text,
                parse_mode='Markdown'
            )

        except Exception as e:
            logger.error(f"Upload error: {e}")
            await update.message.reply_text(f"❌ **ERROR:** `{str(e)}`", parse_mode='Markdown')
        return

    # Button handlers
    if text == "🗳️ UPLOAD MANAGER":
        await update.message.reply_text(
            "🗳️ **UPLOAD MANAGER**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            "📪 **Send your .zip file containing:**\n"
            "• `main.py` (your bot code)\n"
            "• `requirements.txt` (dependencies)\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )

    elif text == "📮 FILE MANAGER":
        user_projects = [p for p, d in project_owners.items() if d["u_id"] == user_id]
        if not user_projects:
            await update.message.reply_text("📮 **NO PROJECTS FOUND**", parse_mode='Markdown')
            return
        keyboard = []
        for p in user_projects:
            status = "💚 ONLINE" if (p in running_processes and running_processes[p].poll() is None) else "💔 OFFLINE"
            keyboard.append([InlineKeyboardButton(f"{status} | {p}", callback_data=f"manage_{p}")])
        await update.message.reply_text(
            "📮 **MY FILE MANAGER**\n━━━━━━━━━━━━━━━━━━━━━",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif text == "🗑️ DELETE MANAGER":
        user_projects = [p for p, d in project_owners.items() if d["u_id"] == user_id]
        if not user_projects:
            await update.message.reply_text("🗑️ **NO PROJECTS**", parse_mode='Markdown')
            return
        keyboard = [[InlineKeyboardButton(f"🗑️ {p}", callback_data=f"del_{p}")] for p in user_projects]
        await update.message.reply_text(
            "🗑️ **SELECT PROJECT TO DELETE:**",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )

    elif "🔄 AUTO RESTART:" in text and is_admin(user_id):
        if "ON" in text:
            auto_restart_mode = True
            await animate(update, context, Loading.restarting(), delay=0.5, final_text="🔄 **AUTO RESTART: ACTIVATED**")
        else:
            auto_restart_mode = False
            await animate(update, context, Loading.restarting(), delay=0.5, final_text="🔄 **AUTO RESTART: DEACTIVATED**")
        await update.message.reply_text("Menu updated!", reply_markup=get_main_keyboard(user_id))

    elif text in ["🔒 LOCK SYSTEM", "🔓 UNLOCK SYSTEM"] and is_admin(user_id):
        if "LOCK" in text and "UNLOCK" not in text:
            bot_locked = True
            await animate(update, context, Loading.executing(), delay=0.3, final_text="🔒 **SYSTEM LOCKED**")
        else:
            bot_locked = False
            await animate(update, context, Loading.executing(), delay=0.3, final_text="🔓 **SYSTEM UNLOCKED**")
        await update.message.reply_text("Menu updated!", reply_markup=get_main_keyboard(user_id))

    elif "🛡️ RECOVERY:" in text and is_admin(user_id):
        if "ON" in text:
            recovery_enabled = True
            await animate(update, context, Loading.recovering(), delay=0.5, final_text="🛡️ **AUTO RECOVERY: ENABLED**")
        else:
            recovery_enabled = False
            await animate(update, context, Loading.recovering(), delay=0.5, final_text="🛡️ **AUTO RECOVERY: DISABLED**")
        await update.message.reply_text("Menu updated!", reply_markup=get_main_keyboard(user_id))

    elif text == "🎬 PROJECT FILE" and is_admin(user_id):
        total_projects = len(project_owners)
        running_count = len([p for p in running_processes.values() if p.poll() is None])
        offline_count = total_projects - running_count
        await update.message.reply_text(
            "🎬 **PROJECT STATUS**\n"
            "━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **TOTAL PROJECTS:** `{total_projects}`\n"
            f"💚 **ONLINE:** `{running_count}`\n"
            f"💔 **OFFLINE:** `{offline_count}`\n"
            f"📺 **LIVE LOGS:** `{'ON' if live_logs_enabled else 'OFF'}`\n"
            "━━━━━━━━━━━━━━━━━━━━━",
            parse_mode='Markdown'
        )

    elif text == "🏩 SYSTEM HEALTH":
        msg = await update.message.reply_text("🏩 **Checking system health...**", parse_mode='Markdown')
        try:
            health_data = await get_system_health()
            if health_data["status"] == "ok":
                msg_text = (
                    "🏩 **SYSTEM HEALTH**\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🖥️ **CPU:** {health_data['cpu']} ({health_data['cpu_cores']} cores)\n"
                    f"🧠 **RAM:** {health_data['ram']} ({health_data['ram_used']}/{health_data['ram_total']})\n"
                    f"💾 **DISK:** {health_data['disk']} ({health_data['disk_used']}/{health_data['disk_total']})\n"
                    f"⏱️ **UPTIME:** {health_data['uptime']}\n"
                    f"📮 **PROJECTS:** {len(project_owners)}\n"
                    f"💚 **RUNNING:** {len([p for p in running_processes.values() if p.poll() is None])}\n"
                    f"🛡️ **RECOVERY:** {'ON' if recovery_enabled else 'OFF'}\n"
                    f"📺 **LIVE LOGS:** {'ON' if live_logs_enabled else 'OFF'}\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "✅ **SYSTEM IS HEALTHY**"
                )
            elif health_data["status"] == "basic":
                msg_text = (
                    "🏩 **SYSTEM HEALTH** (Basic)\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    f"🖥️ **PLATFORM:** {health_data['platform']}\n"
                    f"⚙️ **MACHINE:** {health_data['machine']}\n"
                    f"🔧 **PROCESSOR:** {health_data['processor']}\n"
                    f"🐍 **PYTHON:** {health_data['python_version']}\n"
                    f"📮 **PROJECTS:** {len(project_owners)}\n"
                    f"💚 **RUNNING:** {len([p for p in running_processes.values() if p.poll() is None])}\n"
                    "━━━━━━━━━━━━━━━━━━━━━\n"
                    "⚠️ **Install `psutil` for detailed stats**"
                )
            else:
                msg_text = f"❌ **Health check error:** {health_data.get('error', 'Unknown')}"
            await msg.edit_text(msg_text, parse_mode='Markdown')
        except Exception as e:
            await msg.edit_text(f"❌ **Error:** `{e}`", parse_mode='Markdown')

    elif text == "🌎 SERVER INFO":
        await update.message.reply_text(
            "🌎 **SERVER INFO**\n"
            f"🚀 **PORT:** {PORT}\n"
            f"🛡️ **PLATFORM:** {os.environ.get('PLATFORM', 'Unknown')}\n"
            f"🔄 **AUTO-RESTART:** {'ON' if auto_restart_mode else 'OFF'}\n"
            f"🛡️ **AUTO-RECOVERY:** {'ON' if recovery_enabled else 'OFF'}\n"
            f"📺 **LIVE LOGS:** {'ON' if live_logs_enabled else 'OFF'}\n"
            f"📢 **REQUIRED CHANNEL:** {'Not Set' if not REQUIRED_CHANNEL else REQUIRED_CHANNEL}",
            parse_mode='Markdown'
        )

    elif text == "📠 CONTACT ADMIN":
        contact_keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("📠 Contact Owner", url=f"tg://user?id={PRIMARY_ADMIN_ID}")]
        ])
        await update.message.reply_text(
            f"{ADMIN_DISPLAY_NAME}\n📠 Contact Owner",
            reply_markup=contact_keyboard,
            parse_mode='Markdown'
        )


async def handle_docs(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not await require_channel_join(update, context):
        return
    if bot_locked and not is_admin(user_id):
        return

    doc = update.message.document
    if not doc.file_name.endswith('.zip'):
        await update.message.reply_text("❌ **Please send a .zip file only!**", parse_mode='Markdown')
        return

    msg = await update.message.reply_text(Loading.uploading()[0])
    for frame in Loading.uploading()[1:]:
        await asyncio.sleep(0.8)
        try:
            msg = await context.bot.edit_message_text(
                chat_id=update.effective_chat.id, message_id=msg.message_id, text=frame
            )
        except:
            pass

    temp_dir = os.path.join(BASE_DIR, f"tmp_{user_id}")
    os.makedirs(temp_dir, exist_ok=True)
    zip_path = os.path.join(temp_dir, doc.file_name)

    try:
        file = await doc.get_file()
        await file.download_to_drive(zip_path)
        user_upload_state[user_id] = {
            "path": zip_path,
            "u_name": update.effective_user.full_name,
            "original_name": doc.file_name
        }
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text="🖋️ **NAME YOUR PROJECT**\n━━━━━━━━━━━━━━━━━━━━━\n💬 **Send a name for your project:**",
            parse_mode='Markdown'
        )
    except Exception as e:
        logger.error(f"Download error: {e}")
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id, message_id=msg.message_id, text="❌ **DOWNLOAD FAILED!**", parse_mode='Markdown'
        )


async def button_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    data = query.data.split('_')
    action, p_name = data[0], "_".join(data[1:])
    user_id = update.effective_user.id

    if query.data == "check_join":
        is_member = await check_channel_membership(user_id, context)
        if is_member:
            await query.edit_message_text("✅ **Verification successful! You can now use the bot.**", parse_mode='Markdown')
            await start(update, context)
        else:
            await query.answer("❌ You haven't joined the channel yet!", show_alert=True)
        return

    if action == "run":
        if p_name in running_processes and running_processes[p_name].poll() is None:
            await query.edit_message_text(f"⚠️ **`{p_name}` is already running!**", parse_mode='Markdown')
            return
        folder = os.path.join(BASE_DIR, p_name)
        main_file = os.path.join(folder, "main.py")
        if os.path.exists(main_file):
            try:
                msg = await query.edit_message_text(Loading.executing()[0])
                for frame in Loading.executing()[1:]:
                    await asyncio.sleep(0.4)
                    try:
                        msg = await context.bot.edit_message_text(
                            chat_id=update.effective_chat.id, message_id=msg.message_id, text=frame
                        )
                    except:
                        pass

                proc = subprocess.Popen(
                    [sys.executable, "-u", main_file],
                    cwd=folder,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                    bufsize=1
                )
                running_processes[p_name] = proc
                if live_logs_enabled:
                    log_streamer.start_stream(p_name, proc)
                if auto_restart_mode:
                    asyncio.create_task(monitor_process(p_name, folder))

                keyboard = [
                    [InlineKeyboardButton("▶️ RUN", callback_data=f"run_{p_name}"),
                     InlineKeyboardButton("🛑 STOP", callback_data=f"stop_{p_name}")],
                    [InlineKeyboardButton("📺 VIEW LIVE LOGS", callback_data=f"viewlogs_{p_name}")],
                    [InlineKeyboardButton("🗑️ DELETE", callback_data=f"del_{p_name}")]
                ]
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id,
                    message_id=msg.message_id,
                    text=f"🚀 **`{p_name}` is now ONLINE! 💚**\n\n📺 Click **View Live Logs** to see output.",
                    reply_markup=InlineKeyboardMarkup(keyboard),
                    parse_mode='Markdown'
                )
            except Exception as e:
                await query.edit_message_text(f"❌ **FAILED TO START:** `{str(e)}`", parse_mode='Markdown')
        else:
            await query.edit_message_text("❌ **main.py NOT FOUND!**", parse_mode='Markdown')

    elif action == "stop":
        if p_name in running_processes:
            msg = await query.edit_message_text("🛑 STOPPING: [▰▰▰▰▰▰▰▰▰▰] 100%")
            for t, text in [(0.3, "🛑 STOPPING: [▰▰▰▰▰▰▰▰▱▱] 80%"),
                            (0.3, "🛑 STOPPING: [▰▰▰▰▰▰▰▱▱▱] 60%"),
                            (0.3, "🛑 STOPPING: [▰▰▰▰▰▰▱▱▱▱] 40%")]:
                await asyncio.sleep(t)
                await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id, message_id=msg.message_id, text=text
                )
            try:
                log_streamer.stop_stream(p_name)
                running_processes[p_name].terminate()
                running_processes[p_name].wait(timeout=5)
            except:
                running_processes[p_name].kill()
            del running_processes[p_name]
            for uid, session in list(user_log_sessions.items()):
                if session["project"] == p_name:
                    session["active"] = False
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=f"🛑 **`{p_name}` is now OFFLINE! 💔**",
                parse_mode='Markdown'
            )
        else:
            await query.edit_message_text(f"⚠️ **`{p_name}` was not running**", parse_mode='Markdown')

    elif action == "viewlogs":
        if not live_logs_enabled:
            await query.answer("❌ Live logs are currently turned off!", show_alert=True)
            return
        if p_name not in running_processes or running_processes[p_name].poll() is not None:
            await query.answer("❌ This project is not currently running!", show_alert=True)
            return
        log_msg = await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="📺 **INITIALIZING LIVE CONSOLE...**",
            parse_mode='Markdown'
        )
        success = log_streamer.subscribe(p_name, user_id, update.effective_chat.id, log_msg.message_id)
        if success:
            await query.answer("✅ Live logs started!", show_alert=True)
        else:
            await log_msg.edit_text("❌ **Failed to start log stream!**", parse_mode='Markdown')

    elif action == "del":
        msg = await query.edit_message_text(Loading.deleting()[0])
        for frame in Loading.deleting()[1:]:
            await asyncio.sleep(0.5)
            try:
                msg = await context.bot.edit_message_text(
                    chat_id=update.effective_chat.id, message_id=msg.message_id, text=frame
                )
            except:
                pass
        if p_name in running_processes:
            try:
                log_streamer.stop_stream(p_name)
                running_processes[p_name].terminate()
                running_processes[p_name].wait(timeout=5)
            except:
                pass
            del running_processes[p_name]
        for uid, session in list(user_log_sessions.items()):
            if session["project"] == p_name:
                session["active"] = False
        path = os.path.join(BASE_DIR, p_name)
        if os.path.exists(path):
            shutil.rmtree(path)
        if p_name in project_owners:
            del project_owners[p_name]
        await context.bot.edit_message_text(
            chat_id=update.effective_chat.id,
            message_id=msg.message_id,
            text=f"🗑️ **`{p_name}` DELETED!**",
            parse_mode='Markdown'
        )

    elif action == "manage":
        status = "💚 ONLINE" if (p_name in running_processes and running_processes[p_name].poll() is None) else "💔 OFFLINE"
        keyboard = [
            [InlineKeyboardButton("▶️ RUN", callback_data=f"run_{p_name}"),
             InlineKeyboardButton("🛑 STOP", callback_data=f"stop_{p_name}")],
            [InlineKeyboardButton("📺 VIEW LIVE LOGS", callback_data=f"viewlogs_{p_name}")],
            [InlineKeyboardButton("🗑️ DELETE", callback_data=f"del_{p_name}")]
        ]
        await query.edit_message_text(
            f"📦 **PROJECT:** `{p_name}`\n"
            f"📡 **STATUS:** {status}\n"
            f"📺 **LIVE LOGS:** {'Available' if live_logs_enabled else 'Disabled'}",
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode='Markdown'
        )


# ---- SIGNAL HANDLER ----
def signal_handler(signum, frame):
    logger.info("Shutdown signal received, stopping recovery...")
    recovery_system.stop()
    for p_name in list(log_streamer.active_streams.keys()):
        log_streamer.stop_stream(p_name)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)


# ---- MAIN ----
def main():
    web_thread = Thread(target=run_web, daemon=True)
    web_thread.start()

    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.Document.ZIP, handle_docs))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CallbackQueryHandler(button_callback))

    logger.info("Bot started!")

    async def post_init(app):
        asyncio.create_task(log_viewer_task(app))
        asyncio.create_task(recovery_system.start_recovery_monitor(app))

    application.post_init = post_init

    webhook_url = os.environ.get('WEBHOOK_URL')
    if webhook_url:
        application.run_webhook(listen="0.0.0.0", port=PORT, webhook_url=webhook_url)
    else:
        application.run_polling(drop_pending_updates=True)


if __name__ == '__main__':
    main()
