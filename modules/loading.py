import asyncio


class Loading:
    """Loading animation frames for various actions"""

    @staticmethod
    def executing():
        return [
            "🌺 EXECUTING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "🌼 EXECUTING: [▰▱▱▱▱▱▱▱▱▱] 10%",
            "🌻 EXECUTING: [▰▰▱▱▱▱▱▱▱▱] 20%",
            "🌸 EXECUTING: [▰▰▰▱▱▱▱▱▱▱] 30%",
            "🌹 EXECUTING: [▰▰▰▰▱▱▱▱▱▱] 40%",
            "🍁 EXECUTING: [▰▰▰▰▰▱▱▱▱▱] 50%",
            "🌿 EXECUTING: [▰▰▰▰▰▰▱▱▱▱] 60%",
            "🌳 EXECUTING: [▰▰▰▰▰▰▰▱▱▱] 70%",
            "🌲 EXECUTING: [▰▰▰▰▰▰▰▰▱▱] 80%",
            "🪷 EXECUTING: [▰▰▰▰▰▰▰▰▰▱] 90%",
            "✅ COMPLETE:  [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def uploading():
        return [
            "🗳️ UPLOADING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "🗳️ UPLOADING: [▰▱▱▱▱▱▱▱▱▱] 25%",
            "🗳️ UPLOADING: [▰▰▰▱▱▱▱▱▱▱] 50%",
            "🗳️ UPLOADING: [▰▰▰▰▰▰▱▱▱▱] 75%",
            "✅ UPLOAD COMPLETE: [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def installing():
        return [
            "📦 INSTALLING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "📦 INSTALLING: [▰▰▱▱▱▱▱▱▱▱] 20%",
            "📦 INSTALLING: [▰▰▰▰▱▱▱▱▱▱] 40%",
            "📦 INSTALLING: [▰▰▰▰▰▰▱▱▱▱] 60%",
            "📦 INSTALLING: [▰▰▰▰▰▰▰▰▱▱] 80%",
            "✅ INSTALLED:  [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def deleting():
        return [
            "🗑️ DELETING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "🗑️ DELETING: [▰▰▰▱▱▱▱▱▱▱] 30%",
            "🗑️ DELETING: [▰▰▰▰▰▰▱▱▱▱] 60%",
            "✅ DELETED:  [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def restarting():
        return [
            "🔄 RESTARTING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "🔄 RESTARTING: [▰▰▱▱▱▱▱▱▱▱] 20%",
            "🔄 RESTARTING: [▰▰▰▰▱▱▱▱▱▱] 40%",
            "🔄 RESTARTING: [▰▰▰▰▰▰▱▱▱▱] 60%",
            "🔄 RESTARTING: [▰▰▰▰▰▰▰▰▱▱] 80%",
            "✅ RESTARTED:  [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def recovering():
        return [
            "🔄 RECOVERING: [▱▱▱▱▱▱▱▱▱▱] 0%",
            "🔄 RECOVERING: [▰▰▰▱▱▱▱▱▱▱] 30%",
            "🔄 RECOVERING: [▰▰▰▰▰▰▱▱▱▱] 60%",
            "✅ RECOVERED:  [▰▰▰▰▰▰▰▰▰▰] 100%"
        ]

    @staticmethod
    def logs_on():
        return [
            "📺 LIVE LOGS: [▱▱▱▱▱▱▱▱▱▱] OFF",
            "📺 LIVE LOGS: [▰▰▰▱▱▱▱▱▱▱] STARTING...",
            "📺 LIVE LOGS: [▰▰▰▰▰▰▱▱▱▱] CONNECTING...",
            "✅ LIVE LOGS: [▰▰▰▰▰▰▰▰▰▰] ONLINE"
        ]

    @staticmethod
    def logs_off():
        return [
            "📺 LIVE LOGS: [▰▰▰▰▰▰▰▰▰▰] ONLINE",
            "📺 LIVE LOGS: [▰▰▰▰▰▰▱▱▱▱] DISCONNECTING...",
            "📺 LIVE LOGS: [▰▰▰▱▱▱▱▱▱▱] CLOSING...",
            "❌ LIVE LOGS: [▱▱▱▱▱▱▱▱▱▱] OFF"
        ]


async def animate(update, context, frames, delay=0.5, final_text=None):
    """Helper function for loading animation"""
    msg = await update.message.reply_text(frames[0]) if hasattr(update, 'message') else await update.edit_message_text(frames[0])
    for frame in frames[1:]:
        await asyncio.sleep(delay)
        try:
            msg = await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=frame
            )
        except:
            pass
    if final_text:
        await asyncio.sleep(0.3)
        try:
            await context.bot.edit_message_text(
                chat_id=update.effective_chat.id,
                message_id=msg.message_id,
                text=final_text,
                parse_mode='Markdown'
            )
        except:
            pass
    return msg
