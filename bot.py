import asyncio
import logging
import os
import sys
import signal
import subprocess
import threading
from datetime import datetime, timedelta
import uuid
import psutil
from flask import Flask
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler
from pyrogram.errors import FloodWait, ChannelPrivate, MessageDeleteForbidden
from config import API_ID, API_HASH, BOT_TOKEN, SESSION, CHAT_IDS, ID_DUR
from apscheduler.schedulers.asyncio import AsyncIOScheduler

# ============================================================
# ⏱️ AUTO-DELETE TIME CONFIGURATION
# ============================================================
# This bot deletes messages after 15 HOURS by default.
#
# The delete time per chat is set in config.py → ID_DUR dict.
# Each value there is in SECONDS.
#
# Quick reference:
#   15 hours = 54000 seconds  ← current default
#   24 hours = 86400 seconds
#   12 hours = 43200 seconds
#    6 hours = 21600 seconds
#
# The history cleanup window below (DELETE_WINDOW_HOURS) controls
# how far back in history we look when cleaning old messages.
# It should match your delete duration (default: 15 hours).
# ============================================================

DELETE_WINDOW_HOURS = 15  # ← CHANGE THIS if you change your delete duration

# ============================================================
# 🌐 FLASK WEB SERVER (for Render.com deployment)
# ============================================================
# Render requires a web service to bind to a PORT.
# This minimal Flask app keeps the service alive.
# ============================================================

FLASK_PORT = int(os.environ.get("PORT", 8080))

flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    uptime = str(datetime.now() - start_time).split('.')[0]
    return (
        f"<h2>✅ AutoWiper Bot is Running</h2>"
        f"<p>⏳ Uptime: {uptime}</p>"
        f"<p>📌 Monitored Chats: {len(CHAT_IDS)}</p>"
        f"<p>🗑️ Delete Window: {DELETE_WINDOW_HOURS} hours</p>"
    )

@flask_app.route("/health")
def health():
    return {"status": "ok", "uptime": str(datetime.now() - start_time).split('.')[0]}, 200

def run_flask():
    """Run Flask in a background thread so it doesn't block the bot."""
    flask_app.run(host="0.0.0.0", port=FLASK_PORT, use_reloader=False)

# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - 🤖 %(name)s - %(levelname)s - ✨ %(message)s'
)
logger = logging.getLogger(__name__)
start_time = datetime.now()

scheduler = None
app = None
user = None
shutdown_event = None
OWNER_ID = None


async def process_delete(chat_id, msg_id):
    try:
        await app.delete_messages(chat_id, msg_id)
        logger.info(f"🗑️ Deleted message {msg_id} from {chat_id}")
    except (ChannelPrivate, MessageDeleteForbidden):
        logger.warning(f"🔒 Cannot delete message {msg_id} in {chat_id} - no permission")
    except FloodWait as e:
        wait_time = e.value
        logger.warning(f"⏳ FloodWait {wait_time}s for {chat_id}:{msg_id} - retrying after delay")
        await asyncio.sleep(wait_time)
        await process_delete(chat_id, msg_id)
    except Exception as e:
        logger.error(f"💥 Delete failed {chat_id}:{msg_id} - {e}")


def schedule_deletion(chat_id, msg_id, duration):
    """
    Schedule a message for deletion after `duration` seconds.

    ⏱️ duration comes from ID_DUR in config.py (in seconds).
    Default is 54000 seconds = 15 hours.
    """
    if duration:
        job_id = f"delete_{uuid.uuid4().hex}"
        scheduler.add_job(
            process_delete,
            'date',
            run_date=datetime.now() + timedelta(seconds=duration),
            args=[chat_id, msg_id],
            id=job_id,
            misfire_grace_time=300  # allow up to 5 min late execution
        )
        logger.debug(f"⏰ Scheduled deletion of {msg_id} in {duration}s (Job: {job_id})")


async def handle_messages(client, message, is_new=True, duration=None):
    """Handler for new messages — schedules them for auto-deletion."""
    duration = duration or ID_DUR.get(message.chat.id)
    if duration:
        schedule_deletion(message.chat.id, message.id, duration)


async def process_chat_history(chat_id, time_limit):
    """
    Scan recent chat history and schedule old messages for deletion.

    Looks back DELETE_WINDOW_HOURS hours (default: 15 hours).
    """
    try:
        duration = ID_DUR.get(chat_id)
        if not duration:
            logger.info(f"⚠️ No duration set for chat {chat_id}, skipping history cleanup")
            return

        message_count = 0
        processed_ids = set()
        logger.info(f"🔍 Starting history cleanup for chat {chat_id}...")

        async for msg in user.get_chat_history(chat_id, limit=21000):
            if not msg.date or msg.date < time_limit:
                break

            if msg.id in processed_ids:
                continue

            await handle_messages(user, msg, is_new=False, duration=duration)
            processed_ids.add(msg.id)
            message_count += 1

            if message_count % 100 == 0:
                logger.info(f"📊 Processed {message_count} messages in {chat_id}")
                await asyncio.sleep(1)

        logger.info(f"✅ Scheduled {message_count} old messages for deletion in {chat_id}")

    except Exception as e:
        logger.error(f"❌ Failed to process history for {chat_id}: {e}")


async def handle_bot_commands(client, message):
    cmd = message.command[0].lower()

    if cmd == "start":
        await message.reply_text(
            "👋 **Hello! I'm your Group Auto-Cleaner Bot.**\n\n"
            "🗑️ I automatically **delete all messages** after a set time.\n"
            f"⏱️ Current delete window: **{DELETE_WINDOW_HOURS} hours**\n"
            "✨ Keep your groups **clean, clutter-free, and spam-free!**"
        )

    elif cmd == "status":
        uptime = str(datetime.now() - start_time).split('.')[0]
        active_jobs = len(scheduler.get_jobs())

        cpu_percent = psutil.cpu_percent(interval=1)
        per_core = psutil.cpu_percent(interval=1, percpu=True)
        memory = psutil.virtual_memory()
        swap = psutil.swap_memory()
        disk = psutil.disk_usage('/')
        load_avg = psutil.getloadavg() if hasattr(psutil, "getloadavg") else (0, 0, 0)
        processes = len(psutil.pids())

        status_text = (
            f"📊 **Bot Status**\n\n"
            f"⏳ Uptime: `{uptime}`\n"
            f"⚙️ Active Jobs: `{active_jobs}`\n"
            f"📌 Monitored Chats: `{len(CHAT_IDS)}`\n"
            f"🗑️ Delete Window: `{DELETE_WINDOW_HOURS} hours`\n"
            f"🛡️ Status: `🟢 Running`\n\n"
            f"💻 **System Stats**\n"
            f"🔹 CPU Usage: `{cpu_percent}%`\n"
            f"🔹 Per-Core: `{per_core}`\n"
            f"🔹 RAM: `{memory.percent}% of {round(memory.total / (1024**3), 2)} GB`\n"
            f"🔹 Swap: `{swap.percent}% of {round(swap.total / (1024**3), 2)} GB`\n"
            f"🔹 Disk: `{disk.percent}% of {round(disk.total / (1024**3), 2)} GB`\n"
            f"🔹 Load Avg (1m,5m,15m): `{load_avg[0]:.2f}, {load_avg[1]:.2f}, {load_avg[2]:.2f}`\n"
            f"🔹 Processes: `{processes}`"
        )

        await message.reply_text(status_text)

    elif cmd == "ping":
        start = datetime.now()
        msg = await message.reply_text("🏓 Pinging...")
        latency = (datetime.now() - start).total_seconds()
        await msg.edit_text(f"🏓 **Pong!**\n⏱️ Latency: `{latency:.3f}s`")


async def handle_user_commands(client, message):
    if message.from_user.id != OWNER_ID:
        logger.warning(f"🚫 Unauthorized command attempt by user {message.from_user.id}")
        return

    cmd = message.command[0].lower()
    logger.info(f"🛠️ Executing command: /{cmd} from owner")

    if cmd == "delete":
        reply = await message.reply_text("🔄 Processing messages...")
        await delete_messages(reply)

    elif cmd == "update":
        try:
            msg = await message.reply_text("📥 Checking for updates...")
            result = subprocess.run(["git", "pull"], capture_output=True, text=True)

            if result.returncode != 0:
                await msg.edit_text(f"❌ Update failed:\n```\n{result.stderr}\n```")
                return

            await msg.edit_text("✅ Update successful! 🔁 Restarting...")
            os.execl(sys.executable, sys.executable, *sys.argv)

        except Exception as e:
            await message.reply_text(f"💥 Error: `{str(e)}`")

    elif cmd == "restart":
        await message.reply_text("🔁 Restarting bot...")
        os.execl(sys.executable, sys.executable, *sys.argv)

    elif cmd == "chats":
        if not CHAT_IDS:
            await message.reply_text("⚠️ No chats are being monitored.")
        else:
            text = "📌 **Monitored Chats:**\n" + "\n".join([f"🔐 `{cid}`" for cid in CHAT_IDS])
            await message.reply_text(text)


async def delete_messages(reply=None):
    """
    Main cleanup function — scans history of all monitored chats
    and schedules messages older than DELETE_WINDOW_HOURS for deletion.

    ⏱️ DELETE_WINDOW_HOURS is set at the top of this file (default: 15).
    """
    # ── ⏱️ TIME WINDOW FOR HISTORY CLEANUP ──────────────────────────────
    # This line controls how far back we look in chat history.
    # Change DELETE_WINDOW_HOURS (top of file) to adjust.
    time_limit = datetime.now() - timedelta(hours=DELETE_WINDOW_HOURS)
    # ─────────────────────────────────────────────────────────────────────

    tasks = [process_chat_history(chat_id, time_limit) for chat_id in CHAT_IDS]
    await asyncio.gather(*tasks, return_exceptions=True)

    if reply:
        queue_size = sum(1 for job in scheduler.get_jobs() if job.id.startswith("delete_"))
        await reply.edit_text(f"✅ Cleanup complete! 📦 {queue_size} deletions scheduled.")


async def heartbeat():
    while not shutdown_event.is_set():
        try:
            uptime = str(datetime.now() - start_time).split('.')[0]
            active_jobs = len(scheduler.get_jobs())
            logger.info(f"💓 Heartbeat | ⏳ Up: {uptime} | 🛠️ Jobs: {active_jobs}")
            await asyncio.sleep(300)
        except Exception as e:
            logger.error(f"💔 Heartbeat failed: {e}")
            await asyncio.sleep(60)


async def main():
    global app, user, scheduler, shutdown_event, OWNER_ID

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    # APScheduler — do NOT pass event_loop (deprecated in APScheduler 3.x + Python 3.10+)
    scheduler = AsyncIOScheduler()
    scheduler.start()
    scheduler.add_job(delete_messages, 'interval', minutes=4, id="regular_cleanup")
    logger.info("⏰ Scheduler started with regular cleanup every 4 minutes.")

    app = Client("AutoWiperBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)
    user = Client("UserAutoWiper", api_id=API_ID, api_hash=API_HASH, session_string=SESSION)

    app.add_handler(MessageHandler(
        handle_bot_commands,
        filters=filters.command(["start", "status", "ping"]) & filters.private
    ))

    user.add_handler(MessageHandler(
        handle_messages,
        filters=filters.chat(CHAT_IDS) & ~filters.pinned_message
    ))

    user.add_handler(MessageHandler(
        handle_user_commands,
        filters.private & filters.command(["delete", "update", "restart", "chats"])
    ))

    await app.start()
    await user.start()

    me = await user.get_me()
    OWNER_ID = me.id
    logger.info(f"🎯 Owner ID auto-set to: {OWNER_ID} (@{me.username or 'Unknown'})")

    try:
        await user.send_message(
            me.id,
            "✅ **Auto-Cleaner Bot Started!**\n\n"
            f"📊 Monitoring: `{len(CHAT_IDS)}` groups\n"
            f"🗑️ Auto-delete: every `{DELETE_WINDOW_HOURS}` hours\n"
            f"🛠️ Admin commands active for you only.\n"
            f"ℹ️ Use `/status`, `/chats`, `/delete` as needed."
        )
    except Exception as e:
        logger.error(f"📩 Failed to send startup message: {e}")

    heartbeat_task = loop.create_task(heartbeat())

    try:
        await delete_messages()
        logger.info("🚀 Bot is now running! 🌐")

        if not CHAT_IDS:
            logger.warning("⚠️ No CHAT_IDS configured — bot will not monitor any chats.")

        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"💥 Critical error: {e}")

    finally:
        logger.info("🛑 Shutting down gracefully...")

        if 'heartbeat_task' in locals() and not heartbeat_task.done():
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass

        await asyncio.gather(
            app.stop() if app and app.is_connected else asyncio.sleep(0),
            user.stop() if user and user.is_connected else asyncio.sleep(0),
            return_exceptions=True
        )

        if scheduler and scheduler.running:
            scheduler.shutdown()
            logger.info("📋 Scheduler stopped.")

        logger.info("✅ Bot stopped gracefully. Goodbye! 👋")


if __name__ == "__main__":
    # Start Flask web server in background thread (required for Render.com)
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"🌐 Flask web server started on port {FLASK_PORT}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually by user.")
