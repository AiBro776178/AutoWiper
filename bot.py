import asyncio
import logging
import os
import re
import signal
import threading
import uuid
from datetime import datetime, timedelta

from flask import Flask
from pyrogram import Client, filters
from pyrogram.handlers import MessageHandler, CallbackQueryHandler
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait, ChannelPrivate, MessageDeleteForbidden
from apscheduler.schedulers.asyncio import AsyncIOScheduler

import storage
from config import (
    API_ID, API_HASH, BOT_TOKEN, SESSION,
    OWNER_IDS, AUTH_USERS, DEFAULT_DELETE_SECONDS,
)

# ============================================================
# ⏱️ AUTO-DELETE
# ============================================================
# Every MEDIA message (photo, video, document/file, etc.) sent in a
# chat that an authorized (owner/auth) user has registered via /set
# gets auto-deleted after that user's configured timer.
# Default timer: 00:00:04:00 (4 minutes). Text messages are NEVER touched.
# ============================================================

# ============================================================
# 🌐 FLASK WEB SERVER (for Render.com deployment)
# ============================================================

FLASK_PORT = int(os.environ.get("PORT", 8080))
flask_app = Flask(__name__)


@flask_app.route("/")
def home():
    uptime = str(datetime.now() - start_time).split('.')[0]
    total_chats = len(storage.get_all_monitored_chats(_authorized_ids()))
    return (
        f"<h2>✅ AutoWiper Bot is Running</h2>"
        f"<p>⏳ Uptime: {uptime}</p>"
        f"<p>📌 Monitored Chats: {total_chats}</p>"
        f"<p>🗑️ Auto-delete: media only, per-user configurable timer</p>"
    )


@flask_app.route("/health")
def health():
    return {"status": "ok", "uptime": str(datetime.now() - start_time).split('.')[0]}, 200


def run_flask():
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

# In-memory "what is this user currently doing in the /set flow" tracker.
# uid -> "add_channel" | "set_time"
PENDING = {}

NORMAL_MEMBER_MSG = (
    "Sorry, you are a Normal Member. I can't help you.\n"
    "If you want to become a Premium Member, DM: @JapaneseFury\n"
    "Thanks for reaching us."
)

TIME_RE = re.compile(r"^(\d{1,4}):(\d{1,2}):(\d{1,2}):(\d{1,2})$")


# ============================================================
# 🔧 HELPERS
# ============================================================

def _authorized_ids():
    return OWNER_IDS + AUTH_USERS


def is_authorized(user_id):
    return user_id in OWNER_IDS or user_id in AUTH_USERS


def seconds_to_ddhhmmss(total_seconds):
    total_seconds = int(total_seconds)
    days, rem = divmod(total_seconds, 86400)
    hours, rem = divmod(rem, 3600)
    minutes, seconds = divmod(rem, 60)
    return f"{days:02d}:{hours:02d}:{minutes:02d}:{seconds:02d}"


def parse_ddhhmmss(text):
    """Parses 'DD:HH:MM:SS' -> total seconds, or None if invalid."""
    if not text:
        return None
    m = TIME_RE.match(text.strip())
    if not m:
        return None
    dd, hh, mm, ss = (int(x) for x in m.groups())
    if hh > 23 or mm > 59 or ss > 59:
        return None
    total = dd * 86400 + hh * 3600 + mm * 60 + ss
    if total <= 0:
        return None
    return total


def build_set_menu(user_id):
    """Builds the main /set message + keyboard for a given user."""
    info = storage.get_user(user_id)
    channels = info.get("channels", {})
    duration = info.get("duration") or DEFAULT_DELETE_SECONDS
    duration_str = seconds_to_ddhhmmss(duration)

    if not channels:
        text = (
            "⚠️ **You haven't set any channel yet.**\n\n"
            "Please set a channel to start auto-deleting media from it."
        )
        buttons = InlineKeyboardMarkup([
            [InlineKeyboardButton("➕ Add Channel", callback_data="open_manage")]
        ])
        return text, buttons

    lines = [f"{i + 1}. `{cid}` — {title}" for i, (cid, title) in enumerate(channels.items())]
    text = (
        "📋 **Your AutoWiper Settings**\n\n"
        f"📌 **Channels ({len(channels)}):**\n" + "\n".join(lines) + "\n\n"
        f"⏱ **Delete Timer:** `{duration_str}` (DD:HH:MM:SS)\n\n"
        "Tap a channel below to remove it, or manage your settings."
    )

    buttons_rows = []
    for cid, title in channels.items():
        label = f"❌ Remove: {title}"
        if len(label) > 60:
            label = label[:57] + "..."
        buttons_rows.append([InlineKeyboardButton(label, callback_data=f"rm:{cid}")])
    buttons_rows.append([InlineKeyboardButton("⚙️ Manage", callback_data="open_manage")])

    return text, InlineKeyboardMarkup(buttons_rows)


def build_manage_menu():
    text = "⚙️ **Manage Settings**\n\nChoose an option below:"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("➕ Set Channel", callback_data="add_channel")],
        [InlineKeyboardButton("⏱ Set Time", callback_data="set_time")],
        [InlineKeyboardButton("🔙 Back", callback_data="back_to_set")],
    ])
    return text, buttons


# ============================================================
# 🗑️ DELETE ENGINE
# ============================================================

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
    job_id = f"delete_{uuid.uuid4().hex}"
    scheduler.add_job(
        process_delete,
        'date',
        run_date=datetime.now() + timedelta(seconds=duration),
        args=[chat_id, msg_id],
        id=job_id,
        misfire_grace_time=300
    )
    logger.debug(f"⏰ Scheduled deletion of {msg_id} in {duration}s (Job: {job_id})")


def _is_monitored_media(_, __, message):
    chats = storage.get_all_monitored_chats(_authorized_ids())
    return message.chat.id in chats


monitored_media_filter = filters.create(_is_monitored_media)


async def handle_media_message(client, message):
    """New MEDIA message in a monitored chat -> schedule it for deletion."""
    chats = storage.get_all_monitored_chats(_authorized_ids())
    duration = chats.get(message.chat.id, DEFAULT_DELETE_SECONDS)
    schedule_deletion(message.chat.id, message.id, duration)


# ============================================================
# 📜 COMMANDS
# ============================================================

async def handle_start(client, message):
    uid = message.from_user.id if message.from_user else None
    if uid and is_authorized(uid):
        await message.reply_text(
            "👋 **Hello! I'm your Media Auto-Cleaner Bot.**\n\n"
            "🗑️ I automatically **delete media messages** (photos, videos, files/documents) "
            "in the channels & groups you register.\n"
            "⏱️ Default timer: **4 minutes** — fully customizable per user with /set.\n"
            "✍️ Text messages are never touched.\n\n"
            "Use /set to add channels and configure your delete timer."
        )
    else:
        await message.reply_text(NORMAL_MEMBER_MSG)


async def handle_set(client, message):
    uid = message.from_user.id
    if not is_authorized(uid):
        await message.reply_text(NORMAL_MEMBER_MSG)
        return
    text, markup = build_set_menu(uid)
    await message.reply_text(text, reply_markup=markup)


async def handle_status(client, message):
    uptime = str(datetime.now() - start_time).split('.')[0]
    active_jobs = len(scheduler.get_jobs())
    total_chats = len(storage.get_all_monitored_chats(_authorized_ids()))
    text = (
        "📊 **Bot Status**\n\n"
        f"⏳ Uptime: `{uptime}`\n"
        f"⚙️ Active Jobs: `{active_jobs}`\n"
        f"📌 Monitored Chats (all users): `{total_chats}`\n"
        f"🛡️ Status: `🟢 Running`"
    )
    await message.reply_text(text)


async def handle_ping(client, message):
    start = datetime.now()
    msg = await message.reply_text("🏓 Pinging...")
    latency = (datetime.now() - start).total_seconds()
    await msg.edit_text(f"🏓 **Pong!**\n⏱️ Latency: `{latency:.3f}s`")


async def handle_chats(client, message):
    uid = message.from_user.id
    info = storage.get_user(uid)
    channels = info.get("channels", {})
    if not channels:
        await message.reply_text("📌 You haven't set any channels yet. Use /set to add one.")
        return
    duration = info.get("duration") or DEFAULT_DELETE_SECONDS
    lines = [f"{i + 1}. `{cid}` — {title}" for i, (cid, title) in enumerate(channels.items())]
    text = (
        f"📌 **Your Monitored Chats ({len(channels)}):**\n" + "\n".join(lines) +
        f"\n\n⏱ Delete Timer: `{seconds_to_ddhhmmss(duration)}`"
    )
    await message.reply_text(text)


# ============================================================
# 🖲️ CALLBACK BUTTONS (/set flow)
# ============================================================

async def handle_callback(client, callback_query):
    uid = callback_query.from_user.id
    if not is_authorized(uid):
        await callback_query.answer("🚫 You are not authorized.", show_alert=True)
        return

    data = callback_query.data

    if data == "open_manage":
        text, markup = build_manage_menu()
        await callback_query.message.edit_text(text, reply_markup=markup)

    elif data == "back_to_set":
        PENDING.pop(uid, None)
        text, markup = build_set_menu(uid)
        await callback_query.message.edit_text(text, reply_markup=markup)

    elif data == "add_channel":
        PENDING[uid] = "add_channel"
        text = (
            "📥 **Add Channel(s)**\n\n"
            "Send channel/group ID(s), or forward a message from one.\n\n"
            "✨ You can add multiple at once — separate IDs with a comma:\n"
            "`-1004490369392,-1001234567890`\n"
            "No limit, add as many as you want.\n\n"
            "⚠️ Make sure the userbot account is already a member "
            "(admin, so it can delete messages) of each channel/group.\n\n"
            "Send /cancel to cancel."
        )
        await callback_query.message.edit_text(text)

    elif data == "set_time":
        PENDING[uid] = "set_time"
        text = (
            "⏱ **Set Delete Timer**\n\n"
            "Send the time in format `DD:HH:MM:SS` (Days:Hours:Minutes:Seconds).\n\n"
            "Examples:\n"
            "• `00:00:50:00` → 50 minutes\n"
            "• `03:15:00:25` → 3 days 15 hrs 25 sec\n\n"
            "Default: `00:00:04:00` (4 minutes)\n\n"
            "Send /cancel to cancel."
        )
        await callback_query.message.edit_text(text)

    elif data.startswith("rm:"):
        chat_id = data.split(":", 1)[1]
        try:
            await storage.remove_channel(uid, chat_id)
        except Exception as e:
            logger.error(f"💥 Mongo remove_channel failed: {e}")
            await callback_query.answer("❌ Database error, try again.", show_alert=True)
            return
        text, markup = build_set_menu(uid)
        await callback_query.message.edit_text(text, reply_markup=markup)
        await callback_query.answer("✅ Removed")
        return

    await callback_query.answer()


# ============================================================
# ⌨️ PENDING TEXT/FORWARD INPUT (add_channel / set_time replies)
# ============================================================

def _has_pending_action(_, __, message):
    return bool(message.from_user) and message.from_user.id in PENDING


pending_filter = filters.create(_has_pending_action)


async def handle_pending_input(client, message):
    uid = message.from_user.id
    action = PENDING.get(uid)
    if not action:
        return

    if message.text and message.text.strip().lower() == "/cancel":
        PENDING.pop(uid, None)
        await message.reply_text("❌ Cancelled.")
        return

    if action == "add_channel":
        # Case 1: user forwarded a message from a single channel/group.
        if message.forward_from_chat:
            chat_id = message.forward_from_chat.id
            title = message.forward_from_chat.title or str(chat_id)

            try:
                chat = await user.get_chat(chat_id)
                title = chat.title or title or str(chat_id)
                chat_id = chat.id
            except Exception as e:
                await message.reply_text(
                    "❌ Couldn't access that chat. Make sure the userbot account is a member "
                    f"of it and the ID is correct.\n`{e}`"
                )
                return

            try:
                await storage.add_channel(uid, chat_id, title)
            except Exception as e:
                logger.error(f"💥 Mongo add_channel failed: {e}")
                await message.reply_text("❌ Database error while saving. Please try again.")
                return

            PENDING.pop(uid, None)
            await message.reply_text(f"✅ Channel **{title}** (`{chat_id}`) added successfully!")
            return

        # Case 2: user sent one or more channel/group IDs, comma-separated.
        # e.g. -1004490369392  OR  -1004490369392,-1001234567890,-1009876543210
        if not message.text:
            await message.reply_text(
                "❌ Please send the channel ID(s) as text (comma-separated for multiple), "
                "or forward a message from the channel."
            )
            return

        raw_ids = [part.strip() for part in message.text.strip().split(",") if part.strip()]
        if not raw_ids:
            await message.reply_text(
                "❌ Invalid input. Send numeric channel/group ID(s), separated by commas "
                "if more than one. Send /cancel to cancel."
            )
            return

        added, failed, invalid = [], [], []

        for raw_id in raw_ids:
            try:
                cid = int(raw_id)
            except ValueError:
                invalid.append(raw_id)
                continue

            try:
                chat = await user.get_chat(cid)
                title = chat.title or str(chat.id)
                cid = chat.id
            except Exception as e:
                failed.append(f"`{raw_id}` — {e}")
                continue

            try:
                await storage.add_channel(uid, cid, title)
            except Exception as e:
                logger.error(f"💥 Mongo add_channel failed: {e}")
                failed.append(f"`{raw_id}` — database error")
                continue

            added.append(f"✅ **{title}** (`{cid}`)")

        PENDING.pop(uid, None)

        lines = []
        if added:
            lines.append(f"**Added ({len(added)}):**\n" + "\n".join(added))
        if failed:
            lines.append(f"**Failed ({len(failed)}):**\n" + "\n".join(failed))
        if invalid:
            lines.append(f"**Invalid IDs ({len(invalid)}):**\n" + "\n".join(f"`{x}`" for x in invalid))

        await message.reply_text("\n\n".join(lines) if lines else "❌ Nothing was added.")

    elif action == "set_time":
        seconds = parse_ddhhmmss(message.text or "")
        if seconds is None:
            await message.reply_text(
                "❌ Invalid format. Please send time as `DD:HH:MM:SS`.\n"
                "Example: `00:00:50:00` for 50 minutes.\nSend /cancel to cancel."
            )
            return
        try:
            await storage.set_duration(uid, seconds)
        except Exception as e:
            logger.error(f"💥 Mongo set_duration failed: {e}")
            await message.reply_text("❌ Database error while saving. Please try again.")
            return
        PENDING.pop(uid, None)
        await message.reply_text(
            f"✅ Delete timer set to `{seconds_to_ddhhmmss(seconds)}` ({seconds} seconds)."
        )


# ============================================================
# 💓 HEARTBEAT
# ============================================================

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


# ============================================================
# 🚀 MAIN
# ============================================================

async def main():
    global app, user, scheduler, shutdown_event

    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    for sig in (signal.SIGTERM, signal.SIGINT):
        loop.add_signal_handler(sig, lambda: shutdown_event.set())

    scheduler = AsyncIOScheduler()
    scheduler.start()
    logger.info("⏰ Scheduler started.")

    try:
        await storage.init_cache()
        logger.info("🍃 MongoDB cache loaded into memory.")
    except Exception as e:
        logger.error(f"💥 Failed to load MongoDB cache: {e} — check MONGO_URI. Starting with empty cache.")

    app = Client("AutoWiperBot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN, in_memory=True)
    user = Client("UserAutoWiper", api_id=API_ID, api_hash=API_HASH, session_string=SESSION,
                  in_memory=True, no_updates=False)

    # ── Bot (app) commands — all handled in private chat ──
    app.add_handler(MessageHandler(handle_start, filters=filters.command(["start"]) & filters.private))
    app.add_handler(MessageHandler(handle_set, filters=filters.command(["set"]) & filters.private))
    app.add_handler(MessageHandler(handle_status, filters=filters.command(["status"]) & filters.private))
    app.add_handler(MessageHandler(handle_ping, filters=filters.command(["ping"]) & filters.private))
    app.add_handler(MessageHandler(handle_chats, filters=filters.command(["chats"]) & filters.private))
    app.add_handler(CallbackQueryHandler(handle_callback))
    # Catches replies (channel ID / forward / time) while a /set flow is in progress.
    app.add_handler(MessageHandler(
        handle_pending_input,
        filters=filters.private & pending_filter &
                ~filters.command(["start", "set", "status", "ping", "chats"])
    ))

    # ── Userbot (user) — watches monitored chats for media to auto-delete ──
    user.add_handler(MessageHandler(
        handle_media_message,
        filters=filters.media & monitored_media_filter & ~filters.pinned_message
    ))

    await app.start()
    await user.start()

    me = await user.get_me()
    logger.info(f"🎯 Userbot running as: {me.id} (@{me.username or 'Unknown'})")

    try:
        await user.send_message(
            me.id,
            "✅ **Auto-Cleaner Bot Started!**\n\n"
            f"👑 Owners: `{len(OWNER_IDS)}` | 🔑 Auth Users: `{len(AUTH_USERS)}`\n"
            f"📊 Monitoring: `{len(storage.get_all_monitored_chats(_authorized_ids()))}` chats\n"
            f"🗑️ Auto-delete: **media only**, per-user configurable timer (default 4 min)\n"
            f"✍️ Text messages are never deleted."
        )
    except Exception as e:
        logger.error(f"📩 Failed to send startup message: {e}")

    heartbeat_task = loop.create_task(heartbeat())

    logger.info("🚀 Bot is now running! 🌐")
    if not OWNER_IDS and not AUTH_USERS:
        logger.warning("⚠️ No OWNER_IDS / AUTH_USERS configured — nobody can use /set yet.")

    try:
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
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()
    logger.info(f"🌐 Flask web server started on port {FLASK_PORT}")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("🛑 Bot stopped manually by user.")
