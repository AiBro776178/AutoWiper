"""
MongoDB-backed storage for per-user channels & delete-timer settings,
with an in-memory cache for FAST reads on the hot path.

Why a cache?
The media-monitoring filter runs on every single incoming message in every
monitored chat — that's the hottest path in the bot. Hitting MongoDB on every
message would be slow and wasteful. Instead:
  - All WRITES (add/remove channel, set timer) go to MongoDB immediately
    AND update the in-memory cache, so data survives restarts/redeploys.
  - All READS used in the hot path (get_all_monitored_chats) come purely
    from the in-memory cache — zero DB latency.
  - The cache is fully loaded from MongoDB once at startup via init_cache().

One document per user in the "users" collection:
{
  "_id": <user_id>,
  "channels": {"<chat_id>": "Channel Title", ...},
  "duration": 240   # seconds, absent/None = use DEFAULT_DELETE_SECONDS
}
"""

from motor.motor_asyncio import AsyncIOMotorClient

from config import DEFAULT_DELETE_SECONDS, MONGO_URI, MONGO_DB_NAME

_client = None
_collection = None

# In-memory cache: {user_id(int): {"channels": {chat_id(int): title}, "duration": int|None}}
_cache = {}


def _get_collection():
    global _client, _collection
    if _collection is None:
        _client = AsyncIOMotorClient(MONGO_URI)
        _collection = _client[MONGO_DB_NAME]["users"]
    return _collection


async def init_cache():
    """Load all user data from MongoDB into the in-memory cache. Call once at startup."""
    global _cache
    col = _get_collection()
    cache = {}
    async for doc in col.find({}):
        uid = doc["_id"]
        channels = {int(k): v for k, v in doc.get("channels", {}).items()}
        cache[uid] = {"channels": channels, "duration": doc.get("duration")}
    _cache = cache
    return _cache


def get_user(user_id):
    """Fast, in-memory read — no DB hit."""
    info = _cache.get(user_id)
    if not info:
        return {"channels": {}, "duration": None}
    return {"channels": dict(info["channels"]), "duration": info["duration"]}


async def add_channel(user_id, chat_id, title):
    chat_id = int(chat_id)
    col = _get_collection()
    await col.update_one(
        {"_id": user_id},
        {"$set": {f"channels.{chat_id}": title}},
        upsert=True,
    )
    _cache.setdefault(user_id, {"channels": {}, "duration": None})
    _cache[user_id]["channels"][chat_id] = title


async def remove_channel(user_id, chat_id):
    chat_id = int(chat_id)
    col = _get_collection()
    await col.update_one(
        {"_id": user_id},
        {"$unset": {f"channels.{chat_id}": ""}},
    )
    if user_id in _cache and chat_id in _cache[user_id]["channels"]:
        del _cache[user_id]["channels"][chat_id]
        return True
    return False


async def set_duration(user_id, seconds):
    col = _get_collection()
    await col.update_one(
        {"_id": user_id},
        {"$set": {"duration": seconds}},
        upsert=True,
    )
    _cache.setdefault(user_id, {"channels": {}, "duration": None})
    _cache[user_id]["duration"] = seconds


def get_all_monitored_chats(authorized_ids):
    """
    FAST, purely in-memory (no DB hit) — called on every incoming message.

    Merges every currently-authorized user's channels into one dict:
    {chat_id: duration_seconds}.

    If a user is removed from OWNER_IDS/AUTH_USERS, their registered
    channels automatically stop being monitored (filtered out here).
    If the same chat is registered by more than one authorized user, the
    first one found wins for the duration used.
    """
    result = {}
    for uid in authorized_ids:
        info = _cache.get(uid)
        if not info:
            continue
        duration = info.get("duration") or DEFAULT_DELETE_SECONDS
        for cid in info.get("channels", {}):
            if cid not in result:
                result[cid] = duration
    return result
