import os

# ============================================================
# 👑 OWNER & 🔑 AUTH (PREMIUM) USERS
# ============================================================
# Owner(s): unlimited access, full control. No limit on count.
# Auth users: unlimited access too (same power as owner, just
#             not "the owner"). No limit on count.
#
# Set these as comma-separated Telegram user IDs in env vars:
#   OWNER_IDS=123456789,987654321
#   AUTH_USERS=111111111,222222222
# ============================================================

def _parse_ids(env_value):
    return [int(x.strip()) for x in env_value.split(",") if x.strip()]


OWNER_IDS = _parse_ids(os.environ.get("OWNER_IDS", "8909902924"))
AUTH_USERS = _parse_ids(os.environ.get("AUTH_USERS", "8909902924"))

# ============================================================
# ⏱️ DEFAULT AUTO-DELETE DURATION
# ============================================================
# Default is 2 minutes (00:00:00:00 in DD:HH:MM:SS format).
# Each auth/owner user can override this for themselves via /set.
# ============================================================

DEFAULT_DELETE_SECONDS = 2 * 60  # 00:00:02:00

# ============================================================
# 🔑 TELEGRAM API CREDENTIALS (set as environment variables)
# ============================================================
# Set these in your Render.com dashboard (or .env locally):
#   API_ID, API_HASH, BOT_TOKEN
#
# No userbot/SESSION needed anymore — the bot itself (added as admin
# with "Delete messages" permission in each channel/group) both detects
# and deletes media messages directly. Deletion happens well within
# Telegram's window for bot-admin deletions, so no session-based
# userbot is required.
# ============================================================

API_ID = int(os.environ.get("API_ID", "22518279"))
API_HASH = os.environ.get("API_HASH", "61e5cc94bc5e6318643707054e54caf4")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")

# ============================================================
# 🍃 MONGODB (persistent storage for channels & per-user timers)
# ============================================================
# Set MONGO_URI in Render env vars, e.g.:
#   mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
# ============================================================

MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://devms786178_db_user:cEtMdLjmHF5EM2Pf@cluster0.xbqyvnn.mongodb.net/?appName=Cluster0")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "autowiper")
