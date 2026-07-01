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


OWNER_IDS = _parse_ids(os.environ.get("OWNER_IDS", ""))
AUTH_USERS = _parse_ids(os.environ.get("AUTH_USERS", ""))

# ============================================================
# ⏱️ DEFAULT AUTO-DELETE DURATION
# ============================================================
# Default is 4 minutes (00:00:04:00 in DD:HH:MM:SS format).
# Each auth/owner user can override this for themselves via /set.
# ============================================================

DEFAULT_DELETE_SECONDS = 4 * 60  # 00:00:04:00

# ============================================================
# 🔑 TELEGRAM API CREDENTIALS (set as environment variables)
# ============================================================
# Set these in your Render.com dashboard (or .env locally):
#   API_ID, API_HASH, BOT_TOKEN, SESSION
# ============================================================

API_ID = int(os.environ.get("API_ID", "0"))
API_HASH = os.environ.get("API_HASH", "")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "")
SESSION = os.environ.get("SESSION", "")

# ============================================================
# 🍃 MONGODB (persistent storage for channels & per-user timers)
# ============================================================
# Set MONGO_URI in Render env vars, e.g.:
#   mongodb+srv://user:pass@cluster.mongodb.net/?retryWrites=true&w=majority
# ============================================================

MONGO_URI = os.environ.get("MONGO_URI", "")
MONGO_DB_NAME = os.environ.get("MONGO_DB_NAME", "autowiper")
