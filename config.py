# List of channel/group IDs to monitor
CHAT_IDS = [
    -1001111111111,
    -1002222222222
]

# ============================================================
# ⏱️ AUTO-DELETE DURATION SETTINGS (in seconds)
# ============================================================
# DEFAULT DELETE TIME: 15 HOURS = 54000 seconds
#
# To change the delete time, update the value below:
#   15 hours  = 54000  seconds
#   12 hours  = 43200  seconds
#   24 hours  = 86400  seconds
#   6 hours   = 21600  seconds
#   1 hour    = 3600   seconds
#
# Add/remove chat IDs and set their individual timers here.
# ============================================================

DEFAULT_DELETE_SECONDS = 54000  # ← CHANGE THIS to set global default (currently 15 hours)

ID_DUR = {
    -1001111111111: DEFAULT_DELETE_SECONDS,   # 15 hours
    -1002222222222: DEFAULT_DELETE_SECONDS    # 15 hours
}

# Telegram API credentials (replace with your own in private .env or config file)
API_ID = "YOUR_API_ID"
API_HASH = "YOUR_API_HASH"
BOT_TOKEN = "YOUR_BOT_TOKEN"
SESSION = "YOUR_SESSION_STRING"
