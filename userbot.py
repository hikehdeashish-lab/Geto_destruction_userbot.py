import asyncio
import os
import random
import re
import string
import sys
import time
import traceback
import dns.resolver
from datetime import datetime, timezone, timedelta
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from gtts import gTTS

from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEmpty
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PasswordHashInvalidError,
    UserNotParticipantError,
    FloodWaitError,
    UserIsBlockedError,
    PhoneNumberInvalidError,
    PhoneNumberBannedError,
    AboutTooLongError,
    AuthKeyDuplicatedError,
    AuthKeyInvalidError,
    RPCError,
)
from telethon.errors.common import AlreadyInConversationError
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityBlockquote, MessageEntityTextUrl

# ============================================================
#                      CONFIGURATION
# ============================================================

API_ID = int(os.environ.get("API_ID", 36055068))
API_HASH = os.environ.get("API_HASH", "e62c399663de4721efb786f7cfc64022")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8884266307:AAGIdwHBq5Jhl43Q6TDMkNsGgEP6a1K7_T8")
OWNER_ID = int(os.environ.get("OWNER_ID", 8882297263))
LOGGER_ID = int(os.environ.get("LOGGER_ID", -1004380807747))

raw_mongo = (
    os.environ.get("MONGO_URI")
    or os.environ.get("MONGO_URL")
    or os.environ.get("MONGODB_URI")
    or ""
).strip().strip("'").strip('"')

if not raw_mongo:
    raise ValueError("CRITICAL: MONGO_URI Environment Variable nahi mila! Render dashboard me check karein.")

MONGO_URI = raw_mongo
print(f"✅ [DATABASE] Connected to: {MONGO_URI.split('@')[-1] if '@' in MONGO_URI else 'Custom Mongo Host'}")

FORCE_CHANNEL = "ABOUT_GETO"
OWNER_USERNAME = "Bdushdb"

BRAND = "ɢᴇᴛᴏ x ʜᴏꜱᴛᴇʀ"
DISPLAY_BRAND = BRAND
MASTER = "ɢᴇᴛᴏ"
SIGNATURE = "ɢᴇᴛᴏ x ʜᴏꜱᴛᴇʀ"

START_TIME = time.monotonic()
PHOTO_CACHE_PATH = "welcome_photo.jpg"
VIDEO_CACHE_PATH = "welcome_video.mp4"

CACHED_BOT_INFO = {"username": "Ashishxophsjs_bot", "display_name": "ASHISH BOT"}
CACHED_MEDIA = {"type": None, "path": None}

dns.resolver.default_resolver = dns.resolver.Resolver(configure=False)
dns.resolver.default_resolver.nameservers = ["8.8.8.8", "1.1.1.1"]

bot = TelegramClient("ashish_hoster_bot", API_ID, API_HASH)
mongo = AsyncIOMotorClient(MONGO_URI)
db = mongo["AshishHosterV5"]
sessions_col = db["sessions"]
settings_col = db["settings"]
bot_users_col = db["bot_users"]
special_msgs_col = db["special_raid_messages"]
beta_users_col = db["beta_users"]
admins_col = db["admins"]

active_clients = {}
backup_profiles = {}
user_afk_data = {}
user_timebio_tasks = {}

active_raids = {}
active_reply_raids = {}
active_special_raids = {}
active_special_reply_raids = {}
user_special_speeds = {}
auto_user_states = {}
auto_raid_active = {}
u_chup_targets = {}
u_chup_all = {}
u_cleaning_chats = {}

RAID_TEXTS = [
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗖𝗛𝗔𝗞𝗨 𝗗𝗔𝗔𝗟 𝗞𝗔𝗥 𝗖𝗛𝗨𝗧 𝗞𝗔 𝗞𝗛𝗢𝗢𝗡 𝗞𝗔𝗥 𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗧 𝗠𝗘 𝗞𝗘𝗟𝗘 𝗞𝗘 𝗖𝗛𝗜𝗟𝗞𝗘",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗟𝗘𝗧𝗜 𝗠𝗘𝗥𝗜 𝗟𝗨𝗡𝗗 𝗕𝗔𝗗𝗘 𝗠𝗔𝗦𝗧𝗜 𝗦𝗘",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗘𝗡 𝗞𝗢 𝗠𝗘𝗡𝗘 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗕𝗢𝗛𝗢𝗧 𝗦𝗔𝗦𝗧𝗘 𝗦𝗘",
    "𝗧𝗘𝗥𝗘 𝗕𝗔𝗔𝗣 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗",
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗟𝗘𝗞𝗘 𝗕𝗛𝗔𝗚 𝗝𝗔𝗔𝗨𝗡𝗚𝗔",
    "𝗞𝗜𝗗𝗭 𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘",
    "𝗝𝗨𝗡𝗚𝗟𝗘 𝗠𝗘 𝗡𝗔𝗖𝗛𝗧𝗔 𝗛𝗘 𝗠𝗢𝗥𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗠𝗘 𝗥𝗘𝗛𝗧𝗔 𝗛𝗘 𝗦𝗔𝗡𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔",
    "𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗠𝗨𝗝𝗛𝗞𝗢 𝗣𝗔𝗣𝗔 𝗞𝗬𝗢𝗨𝗡𝗞𝗜 𝗠𝗘𝗡𝗘 𝗕𝗔𝗡𝗔𝗗𝗜𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔𝗔 𝗞𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢𝗧𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗣𝗨𝗥𝗔 𝗙𝗔𝗔𝗗 𝗗𝗜𝗔 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗔𝗕𝗕 𝗧𝗘𝗥𝗜 𝗚𝗙 𝗞𝗢 𝗕𝗛𝗘𝗝 😆💦🤤",
    "𝗧𝗘𝗥𝗜 𝗚𝗙 𝗞𝗢 𝗘𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘 𝗧𝗘𝗥𝗜 𝗚𝗙 𝗧𝗢 𝗠𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗕𝗔𝗡𝗚𝗔𝗬𝗜 𝗔𝗕𝗕 𝗖𝗛𝗔𝗟 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗𝗧𝗔 𝗙𝗜𝗥𝗦𝗘 ♥️💦😆😆😆😆",
    "𝗛𝗔𝗥𝗜 𝗛𝗔𝗥𝗜 𝗚𝗛𝗔𝗔𝗦 𝗠𝗘 𝗝𝗛𝗢𝗣𝗗𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 🤣🤣💋💦",
    "𝗖𝗛𝗔𝗟 𝗧𝗘𝗥𝗘 𝗕𝗔𝗔𝗣 𝗞𝗢 𝗕𝗛𝗘𝗝 𝗧𝗘𝗥𝗔 𝗕𝗔𝗦𝗞𝗔 𝗡𝗛𝗜 𝗛𝗘 𝗣𝗔𝗣𝗔 𝗦𝗘 𝗟𝗔𝗗𝗘𝗚𝗔 𝗧𝗨",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗕𝗢𝗠𝗕 𝗗𝗔𝗟𝗞𝗘 𝗨𝗗𝗔 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗞𝗘 𝗟𝗔𝗪𝗗𝗘",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗧𝗥𝗔𝗜𝗡 𝗠𝗘 𝗟𝗘𝗝𝗔𝗞𝗘 𝗧𝗢𝗣 𝗕𝗘𝗗 𝗣𝗘 𝗟𝗜𝗧𝗔𝗞𝗘 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 🤣🤣💋💋",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗘 𝗡𝗨𝗗𝗘𝗦 𝗚𝗢𝗢𝗚𝗟𝗘 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗘𝗪𝗗𝗘 👻🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗩𝗜𝗗𝗘𝗢 𝗕𝗔𝗡𝗔𝗞𝗘 𝗫𝗡𝗫𝗫.𝗖𝗢𝗠 𝗣𝗘 𝗡𝗘𝗘𝗟𝗔𝗠 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗞𝗨𝗧𝗧𝗘 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💦💋",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗞𝗢 𝗣𝗢𝗥𝗡𝗛𝗨𝗕.𝗖𝗢𝗠 𝗣𝗘 𝗨𝗣𝗟𝗢𝗔𝗗 𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔 𝗦𝗨𝗔𝗥 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘 🤣💋💦",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗘𝗞𝗢 𝗖𝗛𝗔𝗞𝗞𝗢 𝗦𝗘 𝗣𝗜𝗟𝗪𝗔𝗩𝗨𝗡𝗚𝗔 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 🤣🤣",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗙𝗔𝗔𝗗𝗞𝗘 𝗥𝗔𝗞𝗗𝗜𝗔 𝗠𝗔‌𝗔‌𝗞𝗘 𝗟𝗢𝗗𝗘 𝗝𝗔𝗔 𝗔𝗕𝗕 𝗦𝗜𝗟𝗪𝗔𝗟𝗘 👄👄",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗘𝗥𝗔 𝗟𝗨𝗡𝗗 𝗞𝗔𝗔𝗟𝗔",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗟𝗘𝗧𝗜 𝗠𝗘𝗥𝗜 𝗟𝗨𝗡𝗗 𝗕𝗔𝗗𝗘 𝗠𝗔𝗦𝗧𝗜 𝗦𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗠𝗘𝗡𝗘 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗕𝗢𝗛𝗢𝗧 𝗦𝗔𝗦𝗧𝗘 𝗦𝗘",
    "𝗕𝗘𝗧𝗘 𝗧𝗨 𝗕𝗔𝗔𝗣 𝗦𝗘 𝗟𝗘𝗚𝗔 𝗣𝗔𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔 𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗞𝗔𝗥𝗞𝗘 𝗡𝗔𝗡𝗚𝗔 💦💋",
    "𝗛𝗔𝗛𝗔𝗛𝗔𝗛 𝗠𝗘𝗥𝗘 𝗕𝗘𝗧𝗘 𝗔𝗚𝗟𝗜 𝗕𝗔𝗔𝗥 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗟𝗘𝗞𝗘 𝗔𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗧 𝗢𝗥 𝗠𝗘𝗥𝗘 𝗠𝗢𝗧𝗘 𝗟𝗨𝗡𝗗 𝗦𝗘 𝗖𝗛𝗨𝗗𝗪𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗥",
    "𝗖𝗛𝗔𝗟 𝗕𝗘𝗧𝗔 𝗧𝗨𝗝𝗛𝗘 𝗠𝗔‌𝗔‌𝗙 𝗞𝗜𝗔 🤣 𝗔𝗕𝗕 𝗔𝗣𝗡𝗜 𝗚𝗙 𝗞𝗢 𝗕𝗛𝗘𝗝",
    "𝗦𝗛𝗔𝗥𝗔𝗠 𝗞𝗔𝗥 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗞𝗜𝗧𝗡𝗔 𝗚𝗔𝗔𝗟𝗜𝗔 𝗦𝗨𝗡𝗪𝗔𝗬𝗘𝗚𝗔 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗔 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗨𝗣𝗘𝗥",
    "𝗔𝗕𝗘 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗔𝗨𝗞𝗔𝗧 𝗡𝗛𝗜 𝗛𝗘𝗧𝗢 𝗔𝗣𝗡𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗟𝗘𝗞𝗘 𝗔𝗔𝗬𝗔 𝗠𝗔𝗧𝗛 𝗞𝗔𝗥 𝗛𝗔𝗛𝗔𝗛𝗔𝗛𝗔",
    "𝗞𝗜𝗗𝗭 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗 𝗖𝗛𝗢𝗗𝗞𝗘 𝗧𝗘𝗥𝗥 𝗟𝗜𝗬𝗘 𝗕𝗛𝗔𝗜 𝗗𝗘𝗗𝗜𝗬𝗔",
    "𝗝𝗨𝗡𝗚𝗟𝗘 𝗠𝗘 𝗡𝗔𝗖𝗛𝗧𝗔 𝗛𝗘 𝗠𝗢𝗥𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗗𝗘𝗞𝗞𝗘 𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗢𝗡𝗖𝗘 𝗠𝗢𝗥𝗘 𝗢𝗡𝗖𝗘 𝗠𝗢𝗥𝗘 🤣🤣💦💋",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗠𝗘 𝗥𝗘𝗛𝗧𝗔 𝗛𝗘 𝗦𝗔𝗡𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗔𝗟𝗔 𝗢𝗥 𝗕𝗔𝗡𝗔 𝗗𝗜𝗔 𝗥𝗔𝗡𝗗 🤤🤣",
    "𝗦𝗔𝗕 𝗕𝗢𝗟𝗧𝗘 𝗠𝗨𝗝𝗛𝗞𝗢 𝗣𝗔𝗣𝗔 𝗞𝗬𝗢𝗨𝗡𝗞𝗜 𝗠𝗘𝗡𝗘 𝗕𝗔𝗡𝗔𝗗𝗜𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧 🤣🤣",
    "𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗦𝗨𝗔𝗥 𝗞𝗔 𝗟𝗢𝗨𝗗𝗔 𝗢𝗥 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗘𝗥𝗔 𝗟𝗢𝗗𝗔",
    "𝗖𝗛𝗔𝗟 𝗖𝗛𝗔𝗟 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗖𝗛𝗜𝗬𝗔 𝗗𝗜𝗞𝗔",
    "𝗛𝗔𝗛𝗔𝗛𝗔𝗛𝗔 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔𝗞𝗢 𝗖𝗛𝗢𝗗 𝗗𝗜𝗔 𝗡𝗔𝗡𝗚𝗔 𝗞𝗔𝗥𝗞𝗘",
    "𝗧𝗘𝗥𝗜 𝗚𝗙 𝗛𝗘 𝗕𝗔𝗗𝗜 𝗦𝗘𝗫𝗬 𝗨𝗦𝗞𝗢 𝗣𝗜𝗟𝗔𝗞𝗘 𝗖𝗛𝗢𝗢𝗗𝗘𝗡𝗚𝗘 𝗣𝗘𝗣𝗦𝗜",
    "2 𝗥𝗨𝗣𝗔𝗬 𝗞𝗜 𝗣𝗘𝗣𝗦𝗜 𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗦𝗔𝗕𝗦𝗘 𝗦𝗘𝗫𝗬 💋💦",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗘𝗘𝗠𝗦 𝗦𝗘 𝗖𝗛𝗨𝗗𝗪𝗔𝗩𝗨𝗡𝗚𝗔 𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💦🤣",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗠𝗘 𝗠𝗨𝗧𝗛𝗞𝗘 𝗙𝗔𝗥𝗔𝗥 𝗛𝗢𝗝𝗔𝗩𝗨𝗡𝗚𝗔 𝗛𝗨𝗜 𝗛𝗨𝗜 𝗛𝗨𝗜",
    "𝗦𝗣𝗘𝗘𝗗 𝗟𝗔𝗔𝗔 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 💋💦🤣",
    "𝗧𝗨𝗝𝗛𝗘 𝗔𝗕 𝗧𝗔𝗞 𝗡𝗔𝗛𝗜 𝗦𝗠𝗝𝗛 𝗔𝗬𝗔 𝗞𝗜 𝗠𝗔𝗜 𝗛𝗜 𝗛𝗨 𝗧𝗨𝗝𝗛𝗘 𝗣𝗔𝗜𝗗𝗔 𝗞𝗔𝗥𝗡𝗘 𝗪𝗔𝗟𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘𝗘 𝗔𝗣𝗡𝗜 𝗠𝗔‌𝗔‌ 𝗦𝗘 𝗣𝗨𝗖𝗛 𝗥Æ𝗡𝗗𝗜 𝗞𝗘 𝗕𝗔𝗖𝗛𝗘𝗘𝗘 🤩👊👤😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗦𝗣𝗢𝗧𝗜𝗙𝗬 𝗗𝗔𝗟 𝗞𝗘 𝗟𝗢𝗙𝗜 𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔 𝗗𝗜𝗡 𝗕𝗛𝗔𝗥 😍🎶🎶💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗡𝗔𝗬𝗔 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗔 𝗞𝗛𝗢𝗟𝗨𝗡𝗚𝗔 𝗖𝗛𝗜𝗡𝗧𝗔 𝗠𝗔𝗧 𝗞𝗔𝗥 👊🤣🤣😳",
    "𝗧𝗘𝗥𝗔 𝗕𝗔𝗔𝗣 𝗛𝗨 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗘 𝗣𝗘 𝗖𝗛𝗨𝗗𝗪𝗔 𝗞𝗘 𝗨𝗦 𝗣𝗔𝗜𝗦𝗘 𝗞𝗜 𝗗𝗔𝗔𝗥𝗨 𝗣𝗘𝗘𝗧𝗔 𝗛𝗨 🍷🤩🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗔𝗣𝗡𝗔 𝗕𝗔𝗗𝗔 𝗦𝗔 𝗟𝗢𝗗𝗔 𝗚𝗛𝗨𝗦𝗦𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗞𝗔𝗟𝗟𝗔𝗔𝗣 𝗞𝗘 𝗠𝗔𝗥 𝗝𝗔𝗬𝗘𝗚𝗜 🤩😳😳🔥",
    "𝗧𝗢𝗛𝗔𝗥 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜 𝗣𝗨𝗥𝗜 𝗞𝗜𝗡𝗚𝗙𝗜𝗦𝗛𝗘𝗥 𝗞𝗜 𝗕𝗢𝗧𝗧𝗟𝗘 𝗗𝗔𝗟 𝗞𝗘 𝗧𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗔𝗡𝗗𝗘𝗥 𝗛𝗜 😱😂🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗞𝗜 𝗦𝗔𝗣𝗡𝗘 𝗠𝗘𝗜 𝗕𝗛𝗜 𝗠𝗘𝗥𝗜 𝗖𝗛𝗨𝗗𝗔𝗜 𝗬𝗔𝗔𝗗 𝗞𝗔𝗥𝗘𝗚𝗜 𝗥Æ𝗡𝗗𝗜 🥳😍👊💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗔𝗨𝗥 𝗕𝗔𝗛𝗘𝗡 𝗞𝗢 𝗗𝗔𝗨𝗗𝗔 𝗗𝗔𝗨𝗗𝗔 𝗡𝗘 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗨𝗡𝗞𝗘 𝗡𝗢 𝗕𝗢𝗟𝗡𝗘 𝗣𝗘 𝗕𝗛𝗜 𝗟𝗔𝗡𝗗 𝗚𝗛𝗨𝗦𝗔 𝗗𝗨𝗡𝗚𝗔 𝗔𝗡𝗗𝗘𝗥 𝗧𝗔𝗞 😎😎🤣🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗢 𝗢𝗡𝗟𝗜𝗡𝗘 𝗢𝗟𝗫 𝗣𝗘 𝗕𝗘𝗖𝗛𝗨𝗡𝗚𝗔 𝗔𝗨𝗥 𝗣𝗔𝗜𝗦𝗘 𝗦𝗘 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗞𝗢𝗧𝗛𝗔 𝗞𝗛𝗢𝗟 𝗗𝗨𝗡𝗚𝗔 😎🤩😝😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗔 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗞𝗜 𝗧𝗨 𝗖𝗔𝗛 𝗞𝗘 𝗕𝗛𝗜 𝗪𝗢 𝗠𝗔𝗦𝗧 𝗖𝗛𝗨𝗗𝗔𝗜 𝗦𝗘 𝗗𝗨𝗥 𝗡𝗛𝗜 𝗝𝗔 𝗣𝗔𝗬𝗘𝗚𝗔𝗔 😏😏🤩😍",
    "𝗦𝗨𝗡 𝗕𝗘 𝗥Æ𝗡𝗗𝗜 𝗞𝗜 𝗔𝗨𝗟𝗔𝗔𝗗 𝗧𝗨 𝗔𝗣𝗡𝗜 𝗕𝗔𝗛𝗘𝗡 𝗦𝗘 𝗦𝗘𝗘𝗞𝗛 𝗞𝗨𝗖𝗛 𝗞𝗔𝗜𝗦𝗘 𝗚𝗔𝗔𝗡𝗗 𝗠𝗔𝗥𝗪𝗔𝗧𝗘 𝗛𝗔𝗜😏🤬🔥💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗬𝗔𝗔𝗥 𝗛𝗨 𝗠𝗘𝗜 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗣𝗬𝗔𝗔𝗥 𝗛𝗨 𝗠𝗘𝗜 𝗔𝗝𝗔 𝗠𝗘𝗥𝗔 𝗟𝗔𝗡𝗗 𝗖𝗛𝗢𝗢𝗦 𝗟𝗘 🤩🤣💥",
    "𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗨𝗦𝗘𝗥𝗕𝗢𝗧 𝗟𝗔𝗚𝗔𝗔𝗨𝗡𝗚𝗔 𝗦𝗔𝗦𝗧𝗘 𝗦𝗣𝗔𝗠 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗦𝗔𝗥𝗜𝗬𝗔 𝗗𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗨𝗦𝗜 𝗦𝗔𝗥𝗜𝗬𝗘 𝗣𝗥 𝗧𝗔𝗡𝗚 𝗞𝗘 𝗕𝗔𝗖𝗛𝗘 𝗣𝗔𝗜𝗗𝗔 𝗛𝗢𝗡𝗚𝗘 😱😱",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 ✋ 𝗛𝗔𝗧𝗧𝗛 𝗗𝗔𝗟𝗞𝗘 👶 𝗕𝗔𝗖𝗛𝗘 𝗡𝗜𝗞𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 😍",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗞𝗘𝗟𝗘 𝗞𝗘 𝗖𝗛𝗜𝗟𝗞𝗘 🤤🤤",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣💋",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦 𝗣𝗘𝗘𝗟𝗔𝗞𝗘 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😚",
    "𝗧𝗘𝗥𝗜 𝗜𝗧𝗘𝗠 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗟𝗨𝗡𝗗 𝗗𝗔𝗔𝗟𝗞𝗘,𝗧𝗘𝗥𝗘 𝗝𝗔𝗜𝗦𝗔 𝗘𝗞 𝗢𝗥 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😆🤤💋",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗟𝗨𝗡𝗗 𝗣𝗥 𝗜𝗧𝗡𝗔 𝗝𝗛𝗨𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗞𝗜 𝗝𝗛𝗨𝗟𝗧𝗘 𝗝𝗛𝗨𝗟𝗧𝗘 𝗛𝗜 𝗕𝗔𝗖𝗛𝗔 𝗣𝗔𝗜𝗗𝗔 𝗞𝗥 𝗗𝗘𝗚𝗜 💦💋",
    "𝗦𝗨𝗔𝗥 𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗦𝗔𝗗𝗔𝗞 𝗣𝗥 𝗟𝗜𝗧𝗔𝗞𝗘 𝗖𝗛𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 😂😆🤤",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗 𝗞𝗥 𝗣𝗜𝗟𝗟𝗘 𝗣𝗔𝗣𝗔 𝗦𝗘 𝗟𝗔𝗗𝗘𝗚𝗔 𝗧𝗨 😼😂🤤",
    "𝗚𝗔𝗟𝗜 𝗚𝗔𝗟𝗜 𝗡𝗘 𝗦𝗛𝗢𝗥 𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗥Æ𝗡𝗗𝗜 𝗖𝗛𝗢𝗥 𝗛𝗘 💋💋💦",
    "𝗔𝗕𝗘 𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗣𝗜𝗟𝗟𝗘 𝗞𝗨𝗧𝗧𝗘 𝗞𝗘 𝗖𝗛𝗢𝗗𝗘 😂👻🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗔𝗜𝗦𝗘 𝗖𝗛𝗢𝗗𝗔 𝗔𝗜𝗦𝗘 𝗖𝗛𝗢𝗗𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗔 𝗕𝗘𝗗 𝗣𝗘𝗛𝗜 𝗠𝗨𝗧𝗛 𝗗𝗜𝗔 💦💦💦💦",
    "𝗧𝗘𝗥𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗔𝗔𝗚 𝗟𝗔𝗚𝗔𝗗𝗜𝗔 𝗠𝗘𝗥𝗔 𝗠𝗢𝗧𝗔 𝗟𝗨𝗡𝗗 𝗗𝗔𝗟𝗞𝗘 🔥🔥💦😆😆",
    "𝗥Æ𝗡𝗗𝗜𝗞𝗘 𝗕𝗔𝗖𝗛𝗛𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗢 𝗖𝗛𝗢𝗗𝗨 𝗖𝗛𝗔𝗟 𝗡𝗜𝗞𝗔𝗟",
    "𝗞𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨 𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧𝗛 𝗔𝗕𝗕 𝗔𝗣𝗡𝗜 𝗕𝗘‌𝗛𝗘𝗡 𝗞𝗢 𝗕𝗛𝗘𝗝 😆👻🤤",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗛𝗢𝗗 𝗞𝗘 𝗨𝗦𝗠𝗘 𝗖𝗬𝗟𝗜𝗡𝗗𝗘𝗥 ⛽️ 𝗙𝗜𝗧 𝗞𝗔𝗥𝗞𝗘 𝗨𝗦𝗠𝗘𝗘 𝗗𝗔𝗟 𝗠𝗔𝗞𝗛𝗔𝗡𝗜 𝗕𝗔𝗡𝗔𝗨𝗡𝗚𝗔𝗔𝗔🤩👊🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗘𝗘𝗦𝗛𝗔 𝗗𝗔𝗟 𝗗𝗨𝗡𝗚𝗔𝗔𝗔 𝗔𝗨𝗥 𝗖𝗛𝗔𝗨𝗥𝗔𝗛𝗘 𝗣𝗘 𝗧𝗔𝗔𝗡𝗚 𝗗𝗨𝗡𝗚𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘😈😱🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗖𝗥𝗘𝗗𝗜𝗧 𝗖𝗔𝗥𝗗 𝗗𝗔𝗟 𝗞𝗘 𝗔𝗚𝗘 𝗦𝗘 500 𝗞𝗘 𝗞𝗔𝗔𝗥𝗘 𝗞𝗔𝗔𝗥𝗘 𝗡𝗢𝗧𝗘 𝗡𝗜𝗞𝗔𝗟𝗨𝗡𝗚𝗔𝗔 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘💰💰🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗦𝗔𝗧𝗛 𝗦𝗨𝗔𝗥 𝗞𝗔 𝗦𝗘𝗫 𝗞𝗔𝗥𝗪𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗘𝗞 𝗦𝗔𝗧𝗛 6-6 𝗕𝗔𝗖𝗛𝗘 𝗗𝗘𝗚𝗜💰🔥😱",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗔𝗣𝗣𝗟𝗘 𝗞𝗔 18𝗪 𝗪𝗔𝗟𝗔 𝗖𝗛𝗔𝗥𝗚𝗘𝗥 🔥🤩",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘𝗜 𝗢𝗡𝗘𝗣𝗟𝗨𝗦 𝗞𝗔 𝗪𝗥𝗔𝗣 𝗖𝗛𝗔𝗥𝗚𝗘𝗥 30𝗪 𝗛𝗜𝗚𝗛 𝗣𝗢𝗪𝗘𝗥 💥😂😎",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗢 𝗔𝗠𝗔𝗭𝗢𝗡 𝗦𝗘 𝗢𝗥𝗗𝗘𝗥 𝗞𝗔𝗥𝗨𝗡𝗚𝗔 10 𝗿𝘀 𝗠𝗘𝗜 𝗔𝗨𝗥 𝗙𝗟𝗜𝗣𝗞𝗔𝗥𝗧 𝗣𝗘 20 𝗥𝗦 𝗠𝗘𝗜 𝗕𝗘𝗖𝗛 𝗗𝗨𝗡𝗚𝗔🤮👿😈🤖",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗕𝗔𝗗𝗜 𝗕𝗛𝗨𝗡𝗗 𝗠𝗘 𝗭𝗢𝗠𝗔𝗧𝗢 𝗗𝗔𝗟 𝗞𝗘 𝗦𝗨𝗕𝗪𝗔𝗬 𝗞𝗔 𝗕𝗙𝗙 𝗩𝗘𝗚 𝗦𝗨𝗕 𝗖𝗢𝗠𝗕𝗢 [15𝗰𝗺 , 16 𝗶𝗻𝗰𝗵𝗲𝘀 ] 𝗢𝗥𝗗𝗘𝗥 𝗖𝗢𝗗 𝗞𝗥𝗩𝗔𝗨𝗡𝗚𝗔 𝗢𝗥 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗝𝗔𝗕 𝗗𝗜𝗟𝗜𝗩𝗘𝗥𝗬 𝗗𝗘𝗡𝗘 𝗔𝗬𝗘𝗚𝗜 𝗧𝗔𝗕 𝗨𝗦𝗣𝗘 𝗝𝗔𝗔𝗗𝗨 𝗞𝗥𝗨𝗡𝗚𝗔 𝗢𝗥 𝗙𝗜𝗥 9 𝗠𝗢𝗡𝗧𝗛 𝗕𝗔𝗔𝗗 𝗩𝗢 𝗘𝗞 𝗢𝗥 𝗙𝗥𝗘𝗘 𝗗𝗜𝗟𝗜𝗩𝗘𝗥𝗬 𝗗𝗘𝗚𝗜🙀👍🥳🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔𝗔𝗟𝗜🙁🤣💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗡𝗚𝗘𝗦 𝗖𝗢𝗠𝗠𝗜𝗧 𝗞𝗥𝗨𝗚𝗔 𝗙𝗜𝗥 𝗧𝗘𝗥𝗜 𝗕𝗛𝗘𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗨𝗧𝗢𝗠𝗔𝗧𝗜𝗖𝗔𝗟𝗟𝗬 𝗨𝗣𝗗𝗔𝗧𝗘 𝗛𝗢𝗝𝗔𝗔𝗬𝗘𝗚𝗜🤖🙏🤔",
    "𝗧𝗘𝗥𝗜 𝗠𝗔𝗨𝗦𝗜 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗜𝗡𝗗𝗜𝗔𝗡 𝗥𝗔𝗜𝗟𝗪𝗔𝗬 🚂💥😂",
    "𝗧𝗨 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗧𝗘𝗥𝗔 𝗞𝗛𝗔𝗡𝗗𝗔𝗡 𝗦𝗔𝗕 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗪𝗗𝗘 𝗥Æ𝗡𝗗𝗜 𝗛𝗔𝗜 𝗥Æ𝗡𝗗𝗜 🤢✅🔥",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗜𝗢𝗡𝗜𝗖 𝗕𝗢𝗡𝗗 𝗕𝗔𝗡𝗔 𝗞𝗘 𝗩𝗜𝗥𝗚𝗜𝗡𝗜𝗧𝗬 𝗟𝗢𝗢𝗦𝗘 𝗞𝗔𝗥𝗪𝗔 𝗗𝗨𝗡𝗚𝗔 𝗨𝗦𝗞𝗜 📚 😎🤩",
    "𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗠𝗔‌𝗔‌ 𝗦𝗘 𝗣𝗨𝗖𝗛𝗡𝗔 𝗕𝗔𝗔𝗣 𝗞𝗔 𝗡𝗔𝗔𝗠 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘𝗘𝗘𝗘𝗘 🤩🥳😳",
    "𝗧𝗨 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗗𝗢𝗡𝗢 𝗞𝗜 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗠𝗘𝗧𝗥𝗢 𝗖𝗛𝗔𝗟𝗪𝗔 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔𝗗𝗔𝗥𝗫𝗛𝗢𝗗 🚇🤩😱🥶",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗜𝗧𝗡𝗔 𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗔 𝗕𝗔𝗔𝗣 𝗕𝗛𝗜 𝗨𝗦𝗞𝗢 𝗣𝗔𝗛𝗖𝗛𝗔𝗡𝗔𝗡𝗘 𝗦𝗘 𝗠𝗔𝗡𝗔 𝗞𝗔𝗥 𝗗𝗘𝗚𝗔😂👿🤩",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗛𝗔𝗜𝗥 𝗗𝗥𝗬𝗘𝗥 𝗖𝗛𝗔𝗟𝗔 𝗗𝗨𝗡𝗚𝗔𝗔💥🔥🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗧𝗘𝗟𝗘𝗚𝗥𝗔𝗠 𝗞𝗜 𝗦𝗔𝗥𝗜 𝗥Æ𝗡𝗗𝗜𝗬𝗢𝗡 𝗞𝗔 𝗥Æ𝗡𝗗𝗜 𝗞𝗛𝗔𝗡𝗔 𝗞𝗛𝗢𝗟 𝗗𝗨𝗡𝗚𝗔𝗔👿🤮😎",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗔𝗟𝗘𝗫𝗔 𝗗𝗔𝗟 𝗞𝗘𝗘 𝗗𝗝 𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔𝗔𝗔 🎶 ⬆️🤩💥",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘𝗜 𝗚𝗜𝗧𝗛𝗨𝗕 𝗗𝗔𝗟 𝗞𝗘 𝗔𝗣𝗡𝗔 𝗕𝗢𝗧 𝗛𝗢𝗦𝗧 𝗞𝗔𝗥𝗨𝗡𝗚𝗔𝗔 🤩👊👤😍",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗩𝗣𝗦 𝗕𝗔𝗡𝗔 𝗞𝗘 24*7 𝗕𝗔𝗦𝗛 𝗖𝗛𝗨𝗗𝗔𝗜 𝗖𝗢𝗠𝗠𝗔𝗡𝗗 𝗗𝗘 𝗗𝗨𝗡𝗚𝗔𝗔 🤩💥🔥🔥",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗧𝗘𝗥𝗘 𝗟𝗔𝗡𝗗 𝗞𝗢 𝗗𝗔𝗟 𝗞𝗘 𝗞𝗔𝗔𝗧 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 🔪😂🔥",
    "𝗦𝗨𝗡 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗕𝗛𝗢𝗦𝗗𝗔 𝗔𝗨𝗥 𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗔 𝗕𝗛𝗜 𝗕𝗛𝗢𝗦𝗗𝗔 👿😎👊",
    "𝗧𝗨𝗝𝗛𝗘 𝗗𝗘𝗞𝗛 𝗞𝗘 𝗧𝗘𝗥𝗜 𝗥Æ𝗡𝗗𝗜 𝗕𝗔𝗛𝗘𝗡 𝗣𝗘 𝗧𝗔𝗥𝗔𝗦 𝗔𝗧𝗔 𝗛𝗔𝗜 𝗠𝗨𝗝𝗛𝗘 𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗢𝗗𝗘𝗘𝗘𝗘 👿💥🤩🔥",
    "𝗦𝗨𝗡 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗝𝗬𝗔𝗗𝗔 𝗡𝗔 𝗨𝗖𝗛𝗔𝗟 𝗠𝗔‌𝗔‌ 𝗖𝗛𝗢𝗗 𝗗𝗘𝗡𝗚𝗘 𝗘𝗞 𝗠𝗜𝗡 𝗠𝗘𝗜 ✅🤣🔥🤩",
    "𝗔𝗣𝗡𝗜 𝗔𝗠𝗠𝗔 𝗦𝗘 𝗣𝗨𝗖𝗛𝗡𝗔 𝗨𝗦𝗞𝗢 𝗨𝗦 𝗞𝗔𝗔𝗟𝗜 𝗥𝗔𝗔𝗧 𝗠𝗘𝗜 𝗞𝗔𝗨𝗡 𝗖𝗛𝗢𝗗𝗡𝗘𝗘 𝗔𝗬𝗔 𝗧𝗛𝗔𝗔𝗔! 𝗧𝗘𝗥𝗘 𝗜𝗦 𝗣𝗔𝗣𝗔 𝗞𝗔 𝗡𝗔𝗔𝗠 𝗟𝗘𝗚𝗜 😂👿😳",
    "𝗧𝗢𝗛𝗔𝗥 𝗕𝗔𝗛𝗜𝗡 𝗖𝗛𝗢𝗗𝗨 𝗕𝗕𝗔𝗛𝗘𝗡 𝗞𝗘 𝗟𝗔𝗪𝗗𝗘 𝗨𝗦𝗠𝗘 𝗠𝗜𝗧𝗧𝗜 𝗗𝗔𝗟 𝗞𝗘 𝗖𝗘𝗠𝗘𝗡𝗧 𝗦𝗘 𝗕𝗛𝗔𝗥 𝗗𝗨 🏠🤢🤩💥",
    "𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗚𝗛𝗨𝗧𝗞𝗔 𝗞𝗛𝗔𝗔𝗞𝗘 𝗧𝗛𝗢𝗢𝗞 𝗗𝗨𝗡𝗚𝗔 🤣🤣",
    "𝗧𝗘𝗥𝗘 𝗕𝗘‌𝗛𝗘𝗡 𝗞 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗖𝗛𝗔𝗞𝗨 𝗗𝗔𝗔𝗟 𝗞𝗔𝗥 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔 𝗞𝗛𝗢𝗢𝗡 𝗞𝗔𝗥 𝗗𝗨𝗚𝗔",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗡𝗛𝗜 𝗛𝗔𝗜 𝗞𝗬𝗔? 9 𝗠𝗔𝗛𝗜𝗡𝗘 𝗥𝗨𝗞 𝗦𝗔𝗚𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗗𝗘𝗧𝗔 𝗛𝗨 🤣🤣🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗘𝗥𝗢𝗣𝗟𝗔𝗡𝗘𝗣𝗔𝗥𝗞 𝗞𝗔𝗥𝗞𝗘 𝗨𝗗𝗔𝗔𝗡 𝗕𝗛𝗔𝗥 𝗗𝗨𝗚𝗔 ✈️🛫",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗨𝗧𝗟𝗜 𝗕𝗢𝗠𝗕 𝗙𝗢𝗗 𝗗𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗝𝗛𝗔𝗔𝗧𝗘 𝗝𝗔𝗟 𝗞𝗘 𝗞𝗛𝗔𝗔𝗞 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜💣",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 𝗦𝗖𝗢𝗢𝗧𝗘𝗥 𝗗𝗔𝗔𝗟 𝗗𝗨𝗚𝗔👅",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗔𝗞𝗧𝗘 🤱 𝗚𝗔𝗟𝗜 𝗞𝗘 𝗞𝗨𝗧𝗧𝗢 🦮 𝗠𝗘 𝗕𝗔𝗔𝗧 𝗗𝗨𝗡𝗚𝗔 𝗣𝗛𝗜𝗥 🍞 𝗕𝗥𝗘𝗔𝗗 𝗞𝗜 𝗧𝗔𝗥𝗛 𝗞𝗛𝗔𝗬𝗘𝗡𝗚𝗘 𝗪𝗢 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧",
    "𝗗𝗨𝗗𝗛 𝗛𝗜𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗘 𝗨𝗣𝗥 𝗡𝗜𝗖𝗛𝗘 🆙🆒😙",
    "𝗧𝗘𝗥𝗜 𝗕𝗘𝗛𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘 @ll_ALPHA_BABY_lll 𝗞𝗔 𝗟𝗨𝗡𝗗 𝗗𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗙𝗜𝗥 𝗢 𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧 𝗛𝗢 𝗝𝗔𝗬𝗘𝗚𝗜 🍌🍌😍",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗗𝗛𝗔𝗡𝗗𝗛𝗘 𝗩𝗔𝗔𝗟𝗜 😋😛",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗔𝗖 𝗟𝗔𝗚𝗔 𝗗𝗨𝗡𝗚𝗔 𝗦𝗔𝗔𝗥𝗜 𝗚𝗔𝗥𝗠𝗜 𝗡𝗜𝗞𝗔𝗟 𝗝𝗔𝗔𝗬𝗘𝗚𝗜",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦 𝗣𝗘𝗘𝗟𝗔𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗😚",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗞𝗢𝗟𝗞𝗔𝗧𝗔 𝗩𝗔𝗔𝗟𝗘 𝗝𝗜𝗧𝗨 𝗕𝗛𝗔𝗜𝗬𝗔 𝗞𝗔 𝗟𝗨𝗡𝗗 𝗠𝗨𝗕𝗔𝗥𝗔𝗞 🤩🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗜 𝗙𝗔𝗡𝗧𝗔𝗦𝗬 𝗛𝗨 𝗟𝗔𝗪𝗗𝗘, 𝗧𝗨 𝗔𝗣𝗡𝗜 𝗕𝗛𝗘𝗡 𝗞𝗢 𝗦𝗠𝗕𝗛𝗔𝗔𝗟 😈😈",
    "𝗧𝗘𝗥𝗔 𝗣𝗘𝗛𝗟𝗔 𝗕𝗔𝗔𝗣 𝗛𝗨 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗘 𝗠𝗘 𝗫𝗩𝗜𝗗𝗘𝗢𝗦.𝗖𝗢𝗠 𝗖𝗛𝗔𝗟𝗔 𝗞𝗘 𝗠𝗨𝗧𝗛 𝗠𝗔‌𝗔‌𝗥𝗨𝗡𝗚𝗔 🤡😹",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗔 𝗚𝗥𝗢𝗨𝗣 𝗩𝗔𝗔𝗟𝗢𝗡 𝗦𝗔𝗔𝗧𝗛 𝗠𝗜𝗟𝗞𝗘 𝗚𝗔𝗡𝗚 𝗕𝗔𝗡𝗚 𝗞𝗥𝗨𝗡𝗚𝗔🙌🏻☠️",
    "𝗧𝗘𝗥𝗜 𝗜𝗧𝗘𝗠 𝗞𝗜 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗟𝗨𝗡𝗗 𝗗𝗔𝗔𝗟𝗞𝗘,𝗧𝗘𝗥𝗘 𝗝𝗔𝗜𝗦𝗔 𝗘𝗞 𝗢𝗥 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗠𝗔‌𝗔‌𝗗𝗔𝗥𝗖𝗛𝗢𝗗🤘🏻🙌🏻☠️",
    "𝗔𝗨𝗞𝗔𝗔𝗧 𝗠𝗘 𝗥𝗘𝗛 𝗩𝗥𝗡𝗔 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘 𝗗𝗔𝗡𝗗𝗔 𝗗𝗔𝗔𝗟 𝗞𝗘 𝗠𝗨𝗛 𝗦𝗘 𝗡𝗜𝗞𝗔𝗔𝗟 𝗗𝗨𝗡𝗚𝗔 𝗦𝗛𝗔𝗥𝗜𝗥 𝗕𝗛𝗜 𝗗𝗔𝗡𝗗𝗘 𝗝𝗘𝗦𝗔 𝗗𝗜𝗞𝗛𝗘𝗚𝗔 🙄🤭🤭",
    "𝗧𝗘𝗥𝗜 𝗠𝗨𝗠𝗠𝗬 𝗞𝗘 𝗦𝗔𝗔𝗧𝗛 𝗟𝗨𝗗𝗢 𝗞𝗛𝗘𝗟𝗧𝗘 𝗞𝗛𝗘𝗟𝗧𝗘 𝗨𝗦𝗞𝗘 𝗠𝗨𝗛 𝗠𝗘 𝗔𝗣𝗡𝗔 𝗟𝗢𝗗𝗔 𝗗𝗘 𝗗𝗨𝗡𝗚𝗔☝🏻☝🏻😬",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗘𝗡 𝗞𝗢 𝗔𝗣𝗡𝗘 𝗟𝗨𝗡𝗗 𝗣𝗥 𝗜𝗧𝗡𝗔 𝗝𝗛𝗨𝗟𝗔𝗔𝗨𝗡𝗚𝗔 𝗞𝗜 𝗝𝗛𝗨𝗟𝗧𝗘 𝗝𝗛𝗨𝗟𝗧𝗘 𝗛𝗜 𝗕𝗔𝗖𝗛𝗔 𝗣𝗔𝗜𝗗𝗔 𝗞𝗥 𝗗𝗘𝗚𝗜👀👯",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗕𝗔𝗧𝗧𝗘𝗥𝗬 𝗟𝗔𝗚𝗔 𝗞𝗘 𝗣𝗢𝗪𝗘𝗥𝗕𝗔𝗡𝗞 𝗕𝗔𝗡𝗔 𝗗𝗨𝗡𝗚𝗔 🔋 🔥🤩",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗖++ 𝗦𝗧𝗥𝗜𝗡𝗚 𝗘𝗡𝗖𝗥𝗬𝗣𝗧𝗜𝗢𝗡 𝗟𝗔𝗚𝗔 𝗗𝗨𝗡𝗚𝗔 𝗕𝗔𝗛𝗧𝗜 𝗛𝗨𝗬𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗥𝗨𝗞 𝗝𝗔𝗬𝗘𝗚𝗜𝗜𝗜𝗜😈🔥😍",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗘 𝗚𝗔𝗔𝗡𝗗 𝗠𝗘𝗜 𝗝𝗛𝗔𝗔𝗗𝗨 𝗗𝗔𝗟 𝗞𝗘 𝗠𝗢𝗥 🦚 𝗕𝗔𝗡𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 🤩🥵😱",
    "𝗧𝗘𝗥𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗛𝗢𝗨𝗟𝗗𝗘𝗥𝗜𝗡𝗚 𝗞𝗔𝗥 𝗗𝗨𝗡𝗚𝗔𝗔 𝗛𝗜𝗟𝗔𝗧𝗘 𝗛𝗨𝗬𝗘 𝗕𝗛𝗜 𝗗𝗔𝗥𝗗 𝗛𝗢𝗚𝗔𝗔𝗔😱🤮👺",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗢 𝗥𝗘𝗗𝗜 𝗣𝗘 𝗕𝗔𝗜𝗧𝗛𝗔𝗟 𝗞𝗘 𝗨𝗦𝗦𝗘 𝗨𝗦𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗕𝗜𝗟𝗪𝗔𝗨𝗡𝗚𝗔𝗔 💰 😵🤩",
    "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 4 𝗛𝗢𝗟𝗘 𝗛𝗔𝗜 𝗨𝗡𝗠𝗘 𝗠𝗦𝗘𝗔𝗟 𝗟𝗔𝗚𝗔 𝗕𝗔𝗛𝗨𝗧 𝗕𝗔𝗛𝗘𝗧𝗜 𝗛𝗔𝗜 𝗕𝗛𝗢𝗙𝗗𝗜𝗞𝗘👊🤮🤢🤢",
    "𝗧𝗘𝗥𝗜 𝗕𝗔𝗛𝗘𝗡 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗕𝗔𝗥𝗚𝗔𝗗 𝗞𝗔 𝗣𝗘𝗗 𝗨𝗚𝗔 𝗗𝗨𝗡𝗚𝗔𝗔 𝗖𝗢𝗥𝗢𝗡𝗔 𝗠𝗘𝗜 𝗦𝗔𝗕 𝗢𝗫𝗬𝗚𝗘𝗡 𝗟𝗘𝗞𝗔𝗥 𝗝𝗔𝗬𝗘𝗡𝗚𝗘🤢🤩🥳",
    "𝗧𝗘𝗥𝗜 𝗠𝗔‌𝗔‌ 𝗞𝗜 𝗖𝗛𝗨𝗨‌𝗧 𝗠𝗘𝗜 𝗦𝗨𝗗𝗢 𝗟𝗔𝗚𝗔 𝗞𝗘 𝗕𝗜𝗚𝗦𝗣𝗔𝗠 𝗟𝗔𝗚𝗔 𝗞𝗘 9999 𝗙𝗨𝗖𝗞 𝗟𝗔𝗚𝗔𝗔 𝗗𝗨 🤩🥳🔥",
    "𝗧𝗘𝗥𝗜 𝗩𝗔𝗛𝗘𝗡 𝗞𝗘 𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘 𝗠𝗘𝗜 𝗕𝗘𝗦𝗔𝗡 𝗞𝗘 𝗟𝗔𝗗𝗗𝗨 𝗕𝗛𝗔𝗥 𝗗𝗨𝗡𝗚𝗔🤩🥳🔥😈",
]

ONE_WORD_RAID_TEXTS = [
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗖𝗛𝗔𝗞𝗨", "𝗗𝗔𝗔𝗟", "𝗞𝗔𝗥", "𝗖𝗛𝗨𝗧", "𝗞𝗔",
    "𝗞𝗛𝗢𝗢𝗡", "𝗞𝗔𝗥", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗞𝗘𝗟𝗘", "𝗞𝗘",
    "𝗖𝗛𝗜𝗟𝗞𝗘", "𝗧𝗘𝗥𝗘", "𝗕𝗔𝗔𝗣", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗞𝗜𝗗𝗭", "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗝𝗨𝗡𝗚𝗟𝗘", "𝗠𝗘", "𝗡𝗔𝗖𝗛𝗧𝗔", "𝗛𝗘", "𝗠𝗢𝗥𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗠𝗘", "𝗥𝗘𝗛𝗧𝗔", "𝗛𝗘", "𝗦𝗔𝗡𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗔𝗟𝗔", "𝗦𝗔𝗕", "𝗕𝗢𝗟𝗧𝗘", "𝗠𝗨𝗝𝗛𝗞𝗢", "𝗣𝗔𝗣𝗔", "𝗞𝗬𝗢𝗨𝗡𝗞𝗜", "𝗠𝗘𝗡𝗘", "𝗕𝗔𝗡𝗔𝗗𝗜𝗔",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗣𝗥𝗘𝗚𝗡𝗘𝗡𝗧", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗠𝗘𝗡𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗔𝗟𝗔",
    "𝗕𝗢𝗛𝗢𝗧", "𝗦𝗔𝗦𝗧𝗘", "𝗦𝗘", "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗞𝗢", "𝗘𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗔", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗘",
    "𝗟𝗢𝗗𝗘", "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗧𝗢", "𝗠𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗕𝗔𝗡𝗚𝗔𝗬𝗜", "𝗔𝗕𝗕", "𝗖𝗛𝗔𝗟", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗𝗧𝗔", "𝗙𝗜𝗥𝗦𝗘", "𝗛𝗔𝗥𝗜", "𝗛𝗔𝗥𝗜", "𝗚𝗛𝗔𝗔𝗦", "𝗠𝗘", "𝗝𝗛𝗢𝗣𝗗𝗔", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗖𝗛𝗔𝗟", "𝗧𝗘𝗥𝗘", "𝗕𝗔𝗔𝗣", "𝗞𝗢", "𝗕𝗛𝗘𝗝", "𝗧𝗘𝗥𝗔", "𝗕𝗔𝗦𝗞𝗔",
    "𝗡𝗛𝗜", "𝗛𝗘", "𝗣𝗔𝗣𝗔", "𝗦𝗘", "𝗟𝗔𝗗𝗘𝗚𝗔", "𝗧𝗨", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗧",
    "𝗠𝗘", "𝗕𝗢𝗠𝗕", "𝗗𝗔𝗟𝗞𝗘", "𝗨𝗗𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗧𝗥𝗔𝗜𝗡", "𝗠𝗘",
    "𝗟𝗘𝗝𝗔𝗞𝗘", "𝗧𝗢𝗣", "𝗕𝗘𝗗", "𝗣𝗘", "𝗟𝗜𝗧𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘",
    "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗩𝗜𝗗𝗘𝗢", "𝗕𝗔𝗡𝗔𝗞𝗘", "𝗫𝗡𝗫𝗫", "𝗣𝗘", "𝗡𝗘𝗘𝗟𝗔𝗠",
    "𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔", "𝗞𝗨𝗧𝗧𝗘", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗞𝗢", "𝗣𝗢𝗥𝗡𝗛𝗨𝗕",
    "𝗣𝗘", "𝗨𝗣𝗟𝗢𝗔𝗗", "𝗞𝗔𝗥𝗗𝗨𝗡𝗚𝗔", "𝗔𝗕𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗞𝗢", "𝗖𝗛𝗢𝗗𝗨", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗕𝗔𝗖𝗛𝗛𝗘",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗙𝗔𝗔𝗗𝗞𝗘", "𝗥𝗔𝗞𝗗𝗜𝗔", "𝗠𝗔𝗔", "𝗞𝗘", "𝗟𝗢𝗗𝗘", "𝗝𝗔𝗔",
    "𝗔𝗕𝗕", "𝗦𝗜𝗟𝗪𝗔𝗟𝗘", "𝗕𝗘𝗧𝗘", "𝗧𝗨", "𝗕𝗔𝗔𝗣", "𝗦𝗘", "𝗟𝗘𝗚𝗔", "𝗣𝗔𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗞𝗔𝗥𝗞𝗘", "𝗡𝗔𝗡𝗚𝗔", "𝗠𝗘𝗥𝗘", "𝗕𝗘𝗧𝗘", "𝗔𝗚𝗟𝗜", "𝗕𝗔𝗔𝗥", "𝗔𝗣𝗡𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗟𝗘𝗞𝗘", "𝗔𝗔𝗬𝗔", "𝗠𝗔𝗧𝗛", "𝗞𝗔𝗥", "𝗖𝗛𝗔𝗟", "𝗕𝗘𝗧𝗔", "𝗧𝗨𝗝𝗛𝗘", "𝗠𝗔𝗔𝗙",
    "𝗞𝗜𝗔", "𝗔𝗕𝗕", "𝗔𝗣𝗡𝗜", "𝗚𝗙", "𝗞𝗢", "𝗕𝗛𝗘𝗝", "𝗔𝗕𝗘", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗕𝗔𝗖𝗛𝗛𝗘", "𝗔𝗨𝗞𝗔𝗧",
    "𝗡𝗛𝗜", "𝗛𝗘𝗧𝗢", "𝗔𝗣𝗡𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗟𝗘𝗞𝗘", "𝗔𝗔𝗬𝗔", "𝗠𝗔𝗧𝗛", "𝗞𝗔𝗥", "𝗞𝗜𝗗𝗭",
    "𝗠𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗖𝗛𝗢𝗗𝗞𝗘", "𝗧𝗘𝗥𝗥", "𝗟𝗜𝗬𝗘", "𝗕𝗛𝗔𝗜", "𝗗𝗘𝗗𝗜𝗬𝗔",
    "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗠𝗘", "𝗥𝗘𝗛𝗧𝗔", "𝗛𝗘", "𝗦𝗔𝗡𝗗", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗",
    "𝗗𝗔𝗟𝗔", "𝗢𝗥", "𝗕𝗔𝗡𝗔", "𝗗𝗜𝗔", "𝗥𝗔𝗡𝗗", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗧", "𝗠𝗘", "𝗠𝗘𝗥𝗔", "𝗟𝗢𝗗𝗔", "𝗖𝗛𝗔𝗟", "𝗖𝗛𝗔𝗟", "𝗔𝗣𝗡𝗜", "𝗠𝗔𝗔", "𝗞𝗜",
    "𝗖𝗛𝗨𝗖𝗛𝗜𝗬𝗔", "𝗗𝗜𝗞𝗔", "𝗕𝗔𝗖𝗛𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗢𝗗", "𝗗𝗜𝗔", "𝗡𝗔𝗡𝗚𝗔", "𝗞𝗔𝗥𝗞𝗘",
    "𝗧𝗘𝗥𝗜", "𝗚𝗙", "𝗛𝗘", "𝗕𝗔𝗗𝗜", "𝗦𝗘𝗫𝗬", "𝗨𝗦𝗞𝗢", "𝗣𝗜𝗟𝗔𝗞𝗘", "𝗖𝗛𝗢𝗢𝗗𝗘𝗡𝗚𝗘", "𝗣𝗘𝗣𝗦𝗜", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗖𝗛𝗘𝗘𝗠𝗦", "𝗦𝗘", "𝗖𝗛𝗨𝗗𝗪𝗔𝗩𝗨𝗡𝗚𝗔", "𝗠𝗔𝗗𝗘𝗥𝗖𝗛𝗢𝗢𝗗", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗦𝗣𝗘𝗘𝗗", "𝗟𝗔𝗔𝗔",
    "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗘𝗡", "𝗖𝗛𝗢𝗗𝗨", "𝗥𝗔𝗡𝗗𝗜𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗔", "𝗕𝗔𝗔𝗣", "𝗛𝗨", "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗥𝗔𝗡𝗗𝗜", "𝗞𝗛𝗔𝗡𝗘", "𝗣𝗘", "𝗖𝗛𝗨𝗗𝗪𝗔", "𝗞𝗘", "𝗨𝗦", "𝗣𝗔𝗜𝗦𝗘", "𝗞𝗜",
    "𝗗𝗔𝗔𝗥𝗨", "𝗣𝗘𝗘𝗧𝗔", "𝗛𝗨", "𝗧𝗢𝗛𝗔𝗥", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗣𝗨𝗥𝗜", "𝗞𝗜",
    "𝗣𝗨𝗥𝗜", "𝗞𝗜𝗡𝗚𝗙𝗜𝗦𝗛𝗘𝗥", "𝗞𝗜", "𝗕𝗢𝗧𝗧𝗟𝗘", "𝗗𝗔𝗟", "𝗞𝗘", "𝗧𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗔𝗡𝗗𝗘𝗥", "𝗛𝗜",
    "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗜𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗞𝗜", "𝗦𝗔𝗣𝗡𝗘", "𝗠𝗘𝗜", "𝗕𝗛𝗜", "𝗠𝗘𝗥𝗜",
    "𝗖𝗛𝗨𝗗𝗔𝗜", "𝗬𝗔𝗔𝗗", "𝗞𝗔𝗥𝗘𝗚𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗔𝗨𝗥", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗢", "𝗗𝗔𝗨𝗗𝗔",
    "𝗗𝗔𝗨𝗗𝗔", "𝗡𝗘", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗢", "𝗢𝗡𝗟𝗜𝗡𝗘", "𝗢𝗟𝗫",
    "𝗣𝗘", "𝗕𝗘𝗖𝗛𝗨𝗡𝗚𝗔", "𝗦𝗨𝗡", "𝗕𝗘", "𝗥𝗔𝗡𝗗𝗜", "𝗞𝗜", "𝗔𝗨𝗟𝗔𝗔𝗗", "𝗧𝗘𝗥𝗜", "𝗕𝗛𝗘𝗡", "𝗞𝗜",
    "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗨𝗦𝗘𝗥𝗕𝗢𝗧", "𝗟𝗔𝗚𝗔𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘", "𝗦𝗔𝗥𝗜𝗬𝗔",
    "𝗗𝗔𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗞𝗘𝗟𝗘", "𝗞𝗘", "𝗖𝗛𝗜𝗟𝗞𝗘",
    "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗢", "𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦", "𝗣𝗘𝗘𝗟𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗔𝗥", "𝗞𝗘", "𝗣𝗜𝗟𝗟𝗘", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗢", "𝗦𝗔𝗗𝗔𝗞", "𝗣𝗥", "𝗟𝗜𝗧𝗔𝗞𝗘", "𝗖𝗛𝗢𝗗", "𝗗𝗨𝗡𝗚𝗔", "𝗚𝗔𝗟𝗜", "𝗚𝗔𝗟𝗜", "𝗡𝗘",
    "𝗦𝗛𝗢𝗥", "𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗥𝗔𝗡𝗗𝗜", "𝗖𝗛𝗢𝗥", "𝗛𝗘", "𝗞𝗜𝗧𝗡𝗔", "𝗖𝗛𝗢𝗗𝗨", "𝗧𝗘𝗥𝗜",
    "𝗥𝗔𝗡𝗗𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗛𝗢𝗗", "𝗞𝗘",
    "𝗨𝗦𝗠𝗘", "𝗖𝗬𝗟𝗜𝗡𝗗𝗘𝗥", "𝗙𝗜𝗧", "𝗞𝗔𝗥𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗦𝗛𝗘𝗘𝗦𝗛𝗔",
    "𝗗𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗖𝗥𝗘𝗗𝗜𝗧", "𝗖𝗔𝗥𝗗", "𝗗𝗔𝗟",
    "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗦𝗔𝗧𝗛", "𝗦𝗨𝗔𝗥", "𝗞𝗔", "𝗦𝗘𝗫", "𝗞𝗔𝗥𝗪𝗔", "𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗔𝗣𝗣𝗟𝗘", "𝗞𝗔", "𝗖𝗛𝗔𝗥𝗚𝗘𝗥", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡",
    "𝗞𝗜", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘𝗜", "𝗢𝗡𝗘𝗣𝗟𝗨𝗦", "𝗞𝗔", "𝗪𝗥𝗔𝗣", "𝗖𝗛𝗔𝗥𝗚𝗘𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜",
    "𝗕𝗔𝗗𝗜", "𝗕𝗛𝗨𝗡𝗗", "𝗠𝗘", "𝗭𝗢𝗠𝗔𝗧𝗢", "𝗗𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗞𝗔𝗔𝗟𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗖𝗛𝗔𝗡𝗚𝗘𝗦", "𝗖𝗢𝗠𝗠𝗜𝗧", "𝗞𝗥𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗨𝗦𝗜", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗜𝗡𝗗𝗜𝗔𝗡", "𝗥𝗔𝗜𝗟𝗪𝗔𝗬", "𝗧𝗨", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗧𝗘𝗥𝗔",
    "𝗞𝗛𝗔𝗡𝗗𝗔𝗡", "𝗦𝗔𝗕", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗟𝗔𝗪𝗗𝗘", "𝗥𝗔𝗡𝗗𝗜", "𝗛𝗔𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡",
    "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗜𝗢𝗡𝗜𝗖", "𝗕𝗢𝗡𝗗", "𝗕𝗔𝗡𝗔", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗠𝗔𝗔",
    "𝗦𝗘", "𝗣𝗨𝗖𝗛𝗡𝗔", "𝗕𝗔𝗔𝗣", "𝗞𝗔", "𝗡𝗔𝗔𝗠", "𝗧𝗨", "𝗔𝗨𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗗𝗢𝗡𝗢",
    "𝗞𝗜", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗠𝗘𝗧𝗥𝗢", "𝗖𝗛𝗔𝗟𝗪𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘",
    "𝗠𝗘𝗜", "𝗛𝗔𝗜𝗥", "𝗗𝗥𝗬𝗘𝗥", "𝗖𝗛𝗔𝗟𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗔𝗟𝗘𝗫𝗔",
    "𝗗𝗔𝗟", "𝗞𝗘", "𝗗𝗝", "𝗕𝗔𝗝𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘𝗜", "𝗚𝗜𝗧𝗛𝗨𝗕",
    "𝗗𝗔𝗟", "𝗞𝗘", "𝗔𝗣𝗡𝗔", "𝗕𝗢𝗧", "𝗛𝗢𝗦𝗧", "𝗞𝗔𝗥𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗧𝗘𝗥𝗘", "𝗟𝗔𝗡𝗗", "𝗞𝗢", "𝗗𝗔𝗟", "𝗞𝗘", "𝗞𝗔𝗔𝗧", "𝗗𝗨𝗡𝗚𝗔", "𝗦𝗨𝗡", "𝗧𝗘𝗥𝗜",
    "𝗠𝗔𝗔", "𝗞𝗔", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗔𝗨𝗥", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗔", "𝗕𝗛𝗜", "𝗕𝗛𝗢𝗦𝗗𝗔", "𝗧𝗨𝗝𝗛𝗘",
    "𝗗𝗘𝗞𝗛", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗥𝗔𝗡𝗗𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗣𝗘", "𝗧𝗔𝗥𝗔𝗦", "𝗔𝗧𝗔", "𝗛𝗔𝗜", "𝗦𝗨𝗡",
    "𝗠𝗔𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗝𝗬𝗔𝗗𝗔", "𝗡𝗔", "𝗨𝗖𝗛𝗔𝗟", "𝗠𝗔𝗔", "𝗖𝗛𝗢𝗗", "𝗗𝗘𝗡𝗚𝗘", "𝗔𝗣𝗡𝗜", "𝗔𝗠𝗠𝗔", "𝗦𝗘",
    "𝗣𝗨𝗖𝗛𝗡𝗔", "𝗧𝗢𝗛𝗔𝗥", "𝗕𝗔𝗛𝗜𝗡", "𝗖𝗛𝗢𝗗𝗨", "𝗕𝗕𝗔𝗛𝗘𝗡", "𝗞𝗘", "𝗟𝗔𝗪𝗗𝗘", "𝗧𝗘𝗥𝗘", "𝗕𝗘𝗛𝗘𝗡", "𝗞",
    "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗖𝗛𝗔𝗞𝗨", "𝗗𝗔𝗔𝗟", "𝗞𝗔𝗥", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘",
    "𝗔𝗘𝗥𝗢𝗣𝗟𝗔𝗡𝗘", "𝗣𝗔𝗥𝗞", "𝗞𝗔𝗥𝗞𝗘", "𝗨𝗗𝗔𝗔𝗡", "𝗕𝗛𝗔𝗥", "𝗗𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘", "𝗦𝗖𝗢𝗢𝗧𝗘𝗥", "𝗗𝗔𝗔𝗟", "𝗗𝗨𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗔𝗞𝗧𝗘", "𝗚𝗔𝗟𝗜",
    "𝗞𝗘", "𝗞𝗨𝗧𝗧𝗢", "𝗠𝗘", "𝗕𝗔𝗔𝗧", "𝗗𝗨𝗡𝗚𝗔", "𝗗𝗨𝗗𝗛", "𝗛𝗜𝗟𝗔𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗘",
    "𝗨𝗣𝗥", "𝗡𝗜𝗖𝗛𝗘", "𝗧𝗘𝗥𝗜", "𝗕𝗘𝗛𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘", "𝗟𝗨𝗡𝗗", "𝗗𝗔𝗟", "𝗗𝗨𝗡𝗚𝗔",
    "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗗𝗛𝗔𝗡𝗗𝗛𝗘", "𝗩𝗔𝗔𝗟𝗜", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘", "𝗔𝗖",
    "𝗟𝗔𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡", "𝗞𝗢", "𝗛𝗢𝗥𝗟𝗜𝗖𝗞𝗦", "𝗣𝗘𝗘𝗟𝗔𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢",
    "𝗞𝗢𝗟𝗞𝗔𝗧𝗔", "𝗩𝗔𝗔𝗟𝗘", "𝗝𝗜𝗧𝗨", "𝗕𝗛𝗔𝗜𝗬𝗔", "𝗞𝗔", "𝗟𝗨𝗡𝗗", "𝗠𝗨𝗕𝗔𝗥𝗔𝗞", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗜",
    "𝗙𝗔𝗡𝗧𝗔𝗦𝗬", "𝗛𝗨", "𝗟𝗔𝗪𝗗𝗘", "𝗧𝗘𝗥𝗔", "𝗣𝗘𝗛𝗟𝗔", "𝗕𝗔𝗔𝗣", "𝗛𝗨", "𝗠𝗔𝗔𝗗𝗔𝗥𝗖𝗛𝗢𝗗", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗘𝗡",
    "𝗞𝗘", "𝗕𝗛𝗢𝗦𝗗𝗘", "𝗠𝗘", "𝗫𝗩𝗜𝗗𝗘𝗢𝗦", "𝗖𝗛𝗔𝗟𝗔", "𝗞𝗘", "𝗠𝗨𝗧𝗛", "𝗠𝗔𝗔𝗥𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗔", "𝗚𝗥𝗢𝗨𝗣", "𝗩𝗔𝗔𝗟𝗢𝗡", "𝗦𝗔𝗔𝗧𝗛", "𝗠𝗜𝗟𝗞𝗘", "𝗚𝗔𝗡𝗚", "𝗕𝗔𝗡𝗚", "𝗞𝗥𝗨𝗡𝗚𝗔", "𝗔𝗨𝗞𝗔𝗔𝗧", "𝗠𝗘",
    "𝗥𝗘𝗛", "𝗩𝗥𝗡𝗔", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘", "𝗗𝗔𝗡𝗗𝗔", "𝗗𝗔𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗨𝗠𝗠𝗬", "𝗞𝗘",
    "𝗦𝗔𝗔𝗧𝗛", "𝗟𝗨𝗗𝗢", "𝗞𝗛𝗘𝗟𝗧𝗘", "𝗞𝗛𝗘𝗟𝗧𝗘", "𝗨𝗦𝗞𝗘", "𝗠𝗨𝗛", "𝗠𝗘", "𝗔𝗣𝗡𝗔", "𝗟𝗢𝗗𝗔", "𝗗𝗘",
    "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗕𝗔𝗧𝗧𝗘𝗥𝗬", "𝗟𝗔𝗚𝗔", "𝗞𝗘", "𝗣𝗢𝗪𝗘𝗥𝗕𝗔𝗡𝗞",
    "𝗕𝗔𝗡𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗖++", "𝗦𝗧𝗥𝗜𝗡𝗚", "𝗘𝗡𝗖𝗥𝗬𝗣𝗧𝗜𝗢𝗡",
    "𝗟𝗔𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗘", "𝗚𝗔𝗔𝗡𝗗", "𝗠𝗘𝗜", "𝗝𝗛𝗔𝗔𝗗𝗨", "𝗗𝗔𝗟", "𝗞𝗘",
    "𝗠𝗢𝗥", "𝗕𝗔𝗡𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗖𝗛𝗨𝗨", "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "𝗦𝗛𝗢𝗨𝗟𝗗𝗘𝗥𝗜𝗡𝗚", "𝗞𝗔𝗥",
    "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗢", "𝗥𝗘𝗗𝗜", "𝗣𝗘", "𝗕𝗔𝗜𝗧𝗛𝗔𝗟", "𝗞𝗘", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔",
    "𝗞𝗜", "𝗖𝗛𝗨𝗨", "𝗠𝗘𝗜", "4", "𝗛𝗢𝗟𝗘", "𝗛𝗔𝗜", "𝗧𝗘𝗥𝗜", "𝗕𝗔𝗛𝗘𝗡", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗕𝗔𝗥𝗚𝗔𝗗", "𝗞𝗔", "𝗣𝗘𝗗", "𝗨𝗚𝗔", "𝗗𝗨𝗡𝗚𝗔", "𝗧𝗘𝗥𝗜", "𝗠𝗔𝗔", "𝗞𝗜", "𝗖𝗛𝗨𝗨",
    "𝗠𝗘𝗜", "𝗦𝗨𝗗𝗢", "𝗟𝗔𝗚𝗔", "𝗞𝗘", "𝗕𝗜𝗚𝗦𝗣𝗔𝗠", "𝗟𝗔𝗚𝗔", "𝗗𝗨", "𝗧𝗘𝗥𝗜", "𝗩𝗔𝗛𝗘𝗡", "𝗞𝗘",
    "𝗕𝗛𝗢𝗦𝗗𝗜𝗞𝗘", "𝗠𝗘𝗜", "𝗕𝗘𝗦𝗔𝗡", "𝗞𝗘", "𝗟𝗔𝗗𝗗𝗨", "𝗕𝗛𝗔𝗥", "𝗗𝗨𝗡𝗚𝗔",
]

PROTECTION_WARNING = "ᴛᴜ ᴀᴩɴᴇ ᴀꜱʜɪꜱʜ ʙᴀᴀᴩ ᴩᴇ ᴜꜱᴇʀʙᴏᴛ ʟᴀɢᴀʏᴇɢᴀ ᴋᴀʀᴜ ᴀʙʜɪ ᴛᴇʀɪ ɢᴜᴅᴅɪ ʟᴀʟ?"

# ============================================================
#                      FONTS & FORMATTING
# ============================================================

CUSTOM_FONT = str.maketrans({
    "a":"ᴀ", "b":"ʙ", "c":"ᴄ", "d":"ᴅ", "e":"ᴇ", "f":"ꜰ",
    "g":"ɢ", "h":"ʜ", "i":"ɪ", "j":"ᴊ", "k":"ᴋ", "l":"ʟ",
    "m":"ᴍ", "n":"ɴ", "o":"ᴏ", "p":"ᴩ", "q":"ǫ", "r":"ʀ",
    "s":"ꜱ", "t":"ᴛ", "u":"ᴜ", "v":"ᴠ", "w":"ᴡ", "x":"x",
    "y":"ʏ", "z":"ᴢ",
    "A":"ᴀ", "B":"ʙ", "C":"ᴄ", "D":"ᴅ", "E":"ᴇ", "F":"ꜰ",
    "G":"ɢ", "H":"ʜ", "I":"ɪ", "J":"ᴊ", "K":"ᴋ", "L":"ʟ",
    "M":"ᴍ", "N":"ɴ", "O":"ᴏ", "P":"ᴩ", "Q":"ǫ", "R":"ʀ",
    "S":"ꜱ", "T":"ᴛ", "U":"ᴜ", "V":"ᴠ", "W":"ᴡ", "X":"x",
    "Y":"ʏ", "Z":"ᴢ",
})

FLIP_MAP = {
    "a": "ɐ", "b": "q", "c": "ɔ", "d": "p", "e": "ǝ", "f": "ɟ", "g": "ƃ", "h": "ɥ",
    "i": "ᴉ", "j": "ɾ", "k": "ʞ", "l": "l", "m": "ɯ", "n": "u", "o": "o", "p": "d",
    "q": "b", "r": "ɹ", "s": "s", "t": "ʇ", "u": "n", "v": "ʌ", "w": "ʍ", "x": "x",
    "y": "ʎ", "z": "z", "A": "∀", "B": "ᗺ", "C": "Ɔ", "D": "ᗡ", "E": "Ǝ", "F": "Ⅎ",
    "G": "⅁", "H": "H", "I": "I", "J": "ſ", "K": "ʞ", "L": "˥", "M": "W", "N": "N",
    "O": "O", "P": "Ԁ", "Q": "Ό", "R": "ᴚ", "S": "S", "T": "⊥", "U": "∩", "V": "Λ",
    "W": "M", "X": "X", "Y": "⅄", "Z": "Z", "?": "¿", "!": "¡", ".": "˙", "_": "‾"
}

def fontify(text: str) -> str:
    saved = []
    def protect(value: str, kind: str) -> str:
        token = f"\x00{kind}{len(saved)}\x00"
        saved.append(value)
        return token

    protected = text.replace(DISPLAY_BRAND, protect(DISPLAY_BRAND, "BRAND"))
    protected = re.sub(r"\.[A-Za-z0-9_]+", lambda m: protect(m.group(0), "CMD"), protected)
    styled = protected.translate(CUSTOM_FONT)

    for i, value in enumerate(saved):
        styled = styled.replace(f"\x00ᴄᴍᴅ{i}\x00", value)
        styled = styled.replace(f"\x00CMD{i}\x00", value)
        styled = styled.replace(f"\x00ʙʀᴀɴᴅ{i}\x00", value)
        styled = styled.replace(f"\x00BRAND{i}\x00", value)
    return styled

def make_glitch_text(text: str) -> str:
    combining_marks = [chr(i) for i in range(0x0300, 0x036F)]
    res = []
    for char in text:
        res.append(char)
        if char.isalnum():
            marks = "".join(random.sample(combining_marks, k=random.randint(2, 4)))
            res.append(marks)
    return "".join(res)

def make_flipped_text(text: str) -> str:
    return "".join(FLIP_MAP.get(ch, ch) for ch in reversed(text))

def utf16_len(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2

def quote_entity(text: str, collapsed: bool = True):
    return MessageEntityBlockquote(offset=0, length=utf16_len(text), collapsed=collapsed)

async def send_card(client_inst, chat_id, text: str, *, collapsed: bool = True, reply_to=None):
    text = fontify(text)
    return await client_inst.send_message(
        chat_id,
        text,
        reply_to=reply_to,
        parse_mode=None,
        formatting_entities=[quote_entity(text, collapsed=collapsed)],
        link_preview=False,
    )

async def reply_card(client_inst, event, text: str, *, collapsed: bool = True):
    reply = await event.get_reply_message()
    reply_target_id = reply.id if reply else None
    try:
        await event.delete()
    except Exception:
        pass
    return await send_card(client_inst, event.chat_id, text, collapsed=collapsed, reply_to=reply_target_id)

async def edit_card(message, text: str, *, collapsed: bool = False):
    text = fontify(text)
    await message.edit(
        text,
        parse_mode=None,
        formatting_entities=[quote_entity(text, collapsed=collapsed)],
        link_preview=False,
    )

async def safe_edit_card(event, text: str, buttons: list, collapsed: bool = False):
    styled = fontify(text)
    entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled), collapsed=collapsed)
    try:
        await event.edit(styled, formatting_entities=[entity], buttons=buttons)
    except Exception:
        try:
            await event.edit(styled, buttons=buttons)
        except Exception:
            pass

async def send_fun_frame(uclient, chat_id, text: str, reply_to=None):
    styled_text = fontify(text)
    entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_text), collapsed=False)
    return await uclient.send_message(
        chat_id,
        styled_text,
        reply_to=reply_to,
        parse_mode=None,
        formatting_entities=[entity],
        link_preview=False
    )

async def edit_fun_frame(msg, text: str):
    styled_text = fontify(text)
    entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_text), collapsed=False)
    await msg.edit(
        styled_text,
        parse_mode=None,
        formatting_entities=[entity],
        link_preview=False
    )

def uptime() -> str:
    total = int(time.monotonic() - START_TIME)
    d, rem = divmod(total, 86400)
    h, rem = divmod(rem, 3600)
    m, s = divmod(rem, 60)
    if d:
        return f"{d}d {h:02d}:{m:02d}:{s:02d}"
    return f"{h:02d}:{m:02d}:{s:02d}"

def header() -> str:
    return f"✨ {BRAND} ✨"

def footer() -> str:
    return f"╰─ {SIGNATURE} ─╯"

def parse_telegram_link(link: str):
    priv_match = re.search(r"t\.me\/c\/(\d+)\/(\d+)", link)
    if priv_match:
        return int("-100" + priv_match.group(1)), int(priv_match.group(2))

    pub_match = re.search(r"t\.me\/([a-zA-Z0-9_]+)\/(\d+)", link)
    if pub_match:
        return pub_match.group(1), int(pub_match.group(2))

    return None, None

async def is_beta_user(user_id: int) -> bool:
    try:
        if int(user_id) == int(OWNER_ID):
            return True
        u = await beta_users_col.find_one({"user_id": int(user_id)})
        return u is not None
    except Exception:
        return False

async def is_protected_user(user_id: int) -> bool:
    try:
        if int(user_id) == int(OWNER_ID):
            return True
        adm = await admins_col.find_one({"user_id": int(user_id)})
        return adm is not None
    except Exception:
        return False

def is_meaningful_message(msg) -> bool:
    if not msg or isinstance(msg, MessageEmpty):
        return False
    if msg.media and getattr(msg, 'sticker', None):
        return False
    
    txt = (msg.text or "").strip()
    if not txt or txt == ".":
        return False
    
    if not re.search(r"[a-zA-Z0-9\u0900-\u097F]", txt):
        return False
    return True

async def fetch_target_latest_message(uclient, chat_id: int, target_user_id: int, fallback_id: int) -> int:
    try:
        async for m in uclient.iter_messages(chat_id, limit=25):
            if m and m.sender_id == target_user_id:
                if is_meaningful_message(m):
                    return m.id
    except Exception:
        pass
    return fallback_id

# ============================================================
#             ERROR LOGGER SYSTEM & LOGOUT
# ============================================================

async def log_to_channel(text: str):
    if not LOGGER_ID:
        return
    try:
        try:
            peer = await bot.get_input_entity(LOGGER_ID)
        except Exception:
            peer = LOGGER_ID

        await bot.send_message(
            peer,
            text,
            formatting_entities=[quote_entity(text, collapsed=False)],
            link_preview=False
        )
    except Exception as e:
        print(f"[Logger Error Handled]: {e}")

async def send_error_log(err: Exception, context: str = "General"):
    tb = "".join(traceback.format_exception(type(err), err, err.__traceback__))
    if len(tb) > 2500:
        tb = tb[-2500:]

    error_card = (
        "⚠️ ╭──「 𝐒ʏꜱᴛᴇᴍ 𝐄ʀʀᴏʀ 𝐃ᴇᴛᴇᴄᴛᴇᴅ 」──╮\n"
        "│\n"
        f"├── 📌 ⇒ 𝐂ᴏɴᴛᴇxᴛ: {context}\n"
        f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        f"├── ❌ ⇒ 𝐄ʀʀᴏʀ: {type(err).__name__} - {str(err)}\n"
        "│\n"
        "├── 📜 𝐓ʀᴀᴄᴇʙᴀᴄᴋ:\n"
        f"`{tb}`\n"
        "│\n"
        "╰────────────────────────────────────╯"
    )
    await log_to_channel(error_card)

def global_exception_handler(loop, context):
    exception = context.get("exception")
    message = context.get("message", "Unhandled Async Loop Error")
    if exception:
        asyncio.create_task(send_error_log(exception, context=message))
    else:
        log_text = f"⚠️ **[ASYNC EVENT ERROR]**\n`{message}`"
        asyncio.create_task(log_to_channel(log_text))

async def perform_logout(user_id: int):
    client_inst = active_clients.pop(user_id, None)
    if client_inst:
        try:
            if client_inst.is_connected():
                await client_inst.disconnect()
        except Exception:
            pass
    await sessions_col.delete_one({"user_id": user_id})

    task = user_timebio_tasks.pop(user_id, None)
    if task:
        task.cancel()

    active_raids.pop(user_id, None)
    active_reply_raids.pop(user_id, None)
    active_special_raids.pop(user_id, None)
    active_special_reply_raids.pop(user_id, None)
    user_special_speeds.pop(user_id, None)
    auto_user_states.pop(user_id, None)
    auto_raid_active.pop(user_id, None)
    u_chup_targets.pop(user_id, None)
    u_chup_all.pop(user_id, None)
    u_cleaning_chats.pop(user_id, None)

    log_msg = (
        "🚪 ╭──「 𝐔sᴇʀʙᴏᴛ 𝐋ᴏɢᴏᴜᴛ 」──╮\n"
        "│\n"
        f"├── 👤 ⇒ 𝐔sᴇʀ ɪ𝐃: `{user_id}`\n"
        f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        "│\n"
        "╰────────────────────────────╯"
    )
    asyncio.create_task(log_to_channel(log_msg))

# ============================================================
#                      UI BUTTONS & TEXTS
# ============================================================

def safe_button(btn_type, text, target, style=None):
    if style:
        try:
            if btn_type == "inline":
                return Button.inline(text, target, style=style)
            elif btn_type == "url":
                return Button.url(text, target, style=style)
        except TypeError:
            pass
    if btn_type == "inline":
        return Button.inline(text, target)
    return Button.url(text, target)

def start_buttons():
    return [
        [safe_button("inline", "「 ʜᴇʟᴩ & ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"menu_help_cats", style="primary")],
        [
            safe_button("url", "「 ᴡᴇʙꜱɪᴛᴇ 」", "http://ashish-intro-web.netlify.app/", style="primary"),
            safe_button("url", "「 ꜱᴜᴩᴩᴏʀᴛ 」", "https://t.me/+gCQ4kgEvubliYzA1", style="primary")
        ],
        [
            safe_button("inline", "「 ʜᴇʟᴩ 」", b"open_help_guide"),
            safe_button("url", "「 ᴍʏ ʜᴏᴍᴇ 」", "https://t.me/+gCQ4kgEvubliYzA1")
        ],
        [safe_button("inline", "「 ʟᴏɢɪɴ ᴜꜱᴇʀʙᴏᴛ 」", b"start_login")],
        [safe_button("url", "「 ᴍʏ ᴍᴀꜱᴛᴇʀ 」", f"https://t.me/{OWNER_USERNAME}", style="danger")]
    ]

def force_join_buttons():
    return [
        [Button.url("「 ᴊᴏɪɴ ᴄʜᴀɴɴᴇʟ 」", f"https://t.me/{FORCE_CHANNEL}")],
        [Button.inline("「 ᴄʜᴇᴄᴋ ᴊᴏɪɴᴇᴅ 」", b"check_joined")]
    ]

HELP_GUIDE_TEXT = fontify(
    "ᴜꜱᴇʀʙᴏᴛ ᴍᴇ ʟᴏɢɪɴ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ʏᴇ ꜱᴛᴇᴩꜱ ꜰᴏʟʟᴏᴡ ᴋᴀʀᴏ\n\n"
    "ꜱᴛᴇᴩ 𝟷 - ʟᴏɢɪɴ ᴜꜱᴇʀʙᴏᴛ ʙᴜᴛᴛᴏɴ ᴩᴇ ᴄʟɪᴄᴋ ᴋᴀʀᴏ ʏᴀ /add ʏᴇ ᴄᴍᴅ ᴅᴀʟᴏ\n\n"
    "ꜱᴛᴇᴩ 𝟸 - ᴀʙ ᴀᴩɴᴀ ɴᴜᴍʙᴇʀ ʙʜᴇᴊᴏ (+919892055312 ᴀɪꜱᴇ)\n\n"
    "ꜱᴛᴇᴩ 𝟹 - ᴀʙ ᴛᴜᴍᴀʀᴇ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ᴩᴇ ᴏᴛᴩ ᴀᴀʏᴀ ʜᴏɢᴀ (1 2 3 4 5 ꜱᴩᴀᴄᴇ ᴅᴇ ᴋᴇ ʟɪᴋʜᴏ)\n\n"
    "ꜱᴛᴇᴩ 𝟺 - ᴀᴄᴄᴏᴜɴᴛ ᴩᴇ ᴩᴀꜱꜱᴡᴏʀᴅ ʟᴀɢᴀ ʜᴜᴀ ʜ ᴛᴏ ᴡᴏ ᴅᴀʟ ᴅᴇɴᴀ, ɴᴀʜɪ ʜ ᴛᴏ ꜱʜɪᴅᴇ ʟᴏɢɪɴ ʜᴏ ᴊᴀʏᴇɢᴀ"
)

CMD_CENTER_TEXT = fontify(
    "ᴀꜱʜɪꜱʜ ᴜꜱᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅ ᴄᴇɴᴛʀᴇ\n\n"
    "𝟷ꜱᴛ ᴩʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟸ɴᴅ ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟹ʀᴅ ꜱᴩᴇᴄɪᴀʟ ᴄᴏᴍᴍᴀɴᴅꜱ (ʙᴇᴛᴀ ᴏɴʟʏ)\n"
    "𝟺ᴛʜ ᴜɴɪǫᴜᴇ ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n"
    "ᴋᴜᴄʜ ꜱᴀᴍᴀᴊʜ ɴᴀʜɪ ᴀᴀʏᴇ ᴛᴏ ꜱᴜᴩᴩᴏʀᴛ ɢᴄ ᴍᴇ ʙᴀᴛᴀ ᴅᴇɴᴀ ❤️"
)

FUN_CMD_TEXT = fontify(
    "🎭 ᴜɴɪǫᴜᴇ ꜰᴜɴ & ᴀɴɪᴍᴀᴛɪᴏɴ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n"
    "• .train - ʟɪᴠᴇ ᴀꜱᴄɪɪ ꜱᴛᴇᴀᴍ ᴛʀᴀɪɴ ᴇɴɢɪɴᴇ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .gadi / .car - ꜱᴩᴏʀᴛꜱ ᴄᴀʀ ʜɪɢʜ ꜱᴩᴇᴇᴅ ᴅʀɪꜰᴛ\n"
    "• .rocket / .launch - ꜱᴩᴀᴄᴇ ʀᴏᴄᴋᴇᴛ ʙʟᴀꜱᴛ-ᴏꜰꜰ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .scan / .hack - ꜰᴀᴋᴇ ᴄʏʙᴇʀ ᴛᴇʀᴍɪɴᴀʟ ʜᴀᴄᴋ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .glitch [text] - ᴢᴀʟɢᴏ / ᴄᴜʀꜱᴇᴅ ᴅᴇᴍᴏɴ ᴛᴇxᴛ ɢᴇɴᴇʀᴀᴛᴏʀ\n"
    "• .matrix - ᴅɪɢɪᴛᴀʟ ʙɪɴᴀʀʏ ᴄᴏᴅᴇ ʀᴀɪɴ ꜱᴛʀᴇᴀᴍ\n"
    "• .bomb - ᴛɪᴄᴋɪɴɢ ᴛɪᴍᴇ ʙᴏᴍʙ ʙʟᴀꜱᴛ ᴇꜰꜰᴇᴄᴛ\n"
    "• .loading [text] - ꜱʟᴇᴇᴋ ꜰᴜᴛᴜʀɪꜱᴛɪᴄ ᴩʀᴏɢʀᴇꜱꜱ ʙᴀʀ\n"
    "• .heart - ᴩᴜʟꜱɪɴɢ ɴᴇᴏɴ ʀᴀɪɴʙᴏᴡ ʜᴇᴀʀᴛ ᴇꜰꜰᴇᴄᴛ\n"
    "• .flip [text] - ᴜᴩꜱɪᴅᴇ-ᴅᴏᴡɴ ɪɴᴠᴇʀᴛᴇᴅ ᴛᴇxᴛ\n\n"
    "⚡ ɴᴏᴛᴇ: ʏᴇ ꜱᴀᴀʀɪ ᴄᴏᴍᴍᴀɴᴅꜱ ʀᴇᴩʟʏ ʙᴀꜱᴇᴅ ʙʜɪ ᴡᴏʀᴋ ᴋᴀʀᴛɪ ʜᴀɪɴ!"
)

SPECIAL_CMD_HEADER_TEXT = fontify(
    "ꜱᴜɴ ʟᴀᴡᴅᴇ ᴀᴄʜᴇ ꜱᴇ ᴩᴀᴅ ʟɪʏᴏ ʏᴇ ʜᴇʟᴩ ᴍᴇꜱɢ ᴏʀ ᴋᴀɪ ᴇxᴩᴏꜱᴇ ʜᴏ ᴋᴇ ᴀᴀʏᴀ ᴛᴏʜ ᴛᴇʀɪ ɢᴀɴᴅ ᴍᴀʀ ʟᴜɴɢᴀ\n\n"
    "ᴋᴏɪ ᴄᴍᴅ ꜱᴀᴍᴊ ɴᴀʜɪ ᴀᴀʏᴇ ᴛᴏʜ ᴍᴜᴊʜᴇ ᴅᴍ ᴍᴀɪ ᴩᴜᴄʜ ʟɪʏᴏ"
)

SPECIAL_RAID_INFO = fontify(
    "ʀᴀɪᴅ - ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱɢ ᴩᴇ ᴛᴀɢ ᴋᴀʀ ᴋᴇ ʙᴏʟ ᴛᴇʀɪ ᴍᴀᴀ ᴅɪ ꜰᴜᴅɪ\n"
    "ꜰɪʀ ʀᴀɪᴅ ꜱᴛᴀʀᴛ ʜᴏ ᴊᴀʏᴇɢɪ\n\n"
    "ʀᴀɪᴅ ᴋᴀ 2ɴᴅ ꜰᴇᴀᴛᴜʀᴇ\n"
    "ᴛᴜ ᴛᴀʀɢᴇᴛ ᴋᴏ ᴜꜱ ᴋᴀ ɴᴀᴍᴇ ʟᴇᴋᴇ ᴄᴍᴅ ᴅᴇɢᴀ ʀᴀᴜꜱʜᴀɴ teri ᴍᴀᴀ ᴅɪ ꜰᴜᴅɪ\n\n"
    "⚡ SPEED CONTROL: ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ʟɪᴋʜᴇ .speed 0.5 ʏᴀ .speed 1\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ: .reboot ʏᴀ .stop"
)

SPECIAL_RRAID_INFO = fontify(
    "ʀᴇᴩʟʏ ʀᴀɪᴅ ᴋᴀ ᴜꜱᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱɢ ᴩᴇ ᴏʏᴇ ᴄʜᴀᴍᴍᴀʀ ᴜᴛʜ\n\n"
    "ᴇx - ʀᴀᴜꜱʜᴀɴ ᴄʜᴀᴍᴀʀ ᴜᴛʜ\n\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ: .reboot ʏᴀ .stop"
)

SPECIAL_REBOOT_INFO = fontify(
    "ᴀʟʟ ᴀᴄᴛɪᴠᴇ ʀᴀɪᴅ ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ᴛʏᴩ ᴋᴀʀᴇ .reboot ʏᴀ .stop"
)

SPECIAL_ONEWORD_INFO = fontify(
    "ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ .auto ʟɪᴋʜ ᴋᴇ ᴛᴀʀɢᴇᴛ ᴍᴇꜱɢ ɴɪᴋᴀʟ ᴅᴀʟ ᴛʜᴇɴ ᴜʀ ʀᴀɪᴅ ᴍᴇꜱɢ\n\n"
    "ᴛʜᴇɴ ʀᴀɪᴅ ꜱᴛᴀʀᴛ"
)

SPECIAL_SPAM_INFO = fontify(
    "⚡ ꜱᴩᴇᴄɪᴀʟ ᴜʟᴛʀᴀ ꜱᴩᴀᴍ\n\n"
    ".sspam [count] [text] - ʙɪɴᴀ ʀᴜᴋᴇ ʜᴀɪ ꜱᴩᴇᴇᴅ ꜱᴩᴀᴍ (0.15s)\n\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ: .reboot"
)

ADVANCE_CMD_TEXT = fontify(
    "⚡ ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n"
    "• .purge [count] - ʙᴜʟᴋ ᴍᴇꜱꜱᴀɢᴇꜱ ᴄʟᴇᴀɴᴇʀ\n"
    "• .afk [reason] - ꜱᴍᴀʀᴛ ᴏꜰꜰʟɪɴᴇ ᴍᴏᴅᴇ\n"
    "• .timebio on/off - ʟɪᴠᴇ ɪꜱᴛ ᴄʟᴏᴄᴋ ʙɪᴏ\n"
    "• .tts [text] - ᴛᴇxᴛ ᴋᴏ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ ᴍᴇ ᴄᴏɴᴠᴇʀᴛ ᴋᴀʀᴇ\n"
    "• .type [text] - ʟɪᴠᴇ ᴛʏᴩɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .fuck - ᴄʟᴇᴀɴ ᴀꜱᴄɪɪ ꜰɪɴɢᴇʀ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .auto - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 (ꜱᴍᴀʀᴛ ʟɪɴᴋ ᴛᴀʀɢᴇᴛ)\n"
    "• .stop - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 ꜱᴛᴏᴩ ᴄᴍᴅ\n"
    "• .restart - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 ʀᴇꜱᴜᴍᴇ ᴄᴍᴅ"
)

PRO_CMD_WELCOME = fontify(
    "ᴡᴇʟᴄᴏᴍᴇ ᴩʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ ꜱᴇᴄᴛɪᴏɴ\n\n"
    "ᴊɪꜱ ᴊɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴋᴇ ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ ʏᴀ ᴡᴏ ᴋᴀɪꜱᴇ ᴡᴏʀᴋ ᴋᴀʀᴛɪ ʜ ᴡᴏ ᴅᴇᴋʜɴᴀ ʜᴀɪ ᴛᴏ ᴜꜱ ᴄᴏᴍᴍᴀɴᴅ ᴋᴇ ʙᴜᴛᴛᴏɴ ᴩᴇ ᴄʟɪᴄᴋ ᴋᴀʀᴏ"
)

RAID_CMD_TEXT = fontify(
    "ʀᴀɪᴅ ᴄᴏᴍᴍᴀɴᴅꜱ ᴀɪꜱᴇ ᴜꜱᴇ ᴋᴀʀᴇ\n\n"
    ".raid - ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ʀᴇᴩʟʏ ᴅᴇ ᴋᴇ ʟɪᴋʜᴇ .raid 10\n"
    ".mraid - ʏᴇ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ᴍᴇɴᴛɪᴏɴ + ʀᴇᴩʟʏ ᴅᴇ ᴋᴇ ʀᴀɪᴅ ᴋᴀʀᴇɢɪ\n"
    ".sraid - ᴜʟᴛʀᴀ ꜰᴀꜱᴛ ʀᴀɪᴅ\n\n"
    "ꜱᴛᴏᴩ ᴄᴍᴅ - .reboot"
)

REPLY_RAID_CMD_TEXT = fontify(
    ".rraid - ʀᴇᴩʟʏ ʀᴀɪᴅ ᴋᴀ ᴜꜱᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ʀᴇᴩʟʏ ᴅᴇ ᴋᴇ ʟɪᴋʜᴇ .rraid\n\n"
    "ꜱᴛᴏᴩ ᴄᴍᴅ - .reboot"
)

SPAM_CMD_TEXT = fontify(
    "ꜱᴩᴀᴍ ᴄᴍᴅ ᴜꜱᴇ ᴀɪꜱᴇ ᴋᴀʀᴛᴇ ʜ (ꜱᴩᴇᴇᴅ: 0.3ꜱ)\n\n"
    ".spam 10 text (ᴊᴏ ᴍᴇꜱꜱᴀɢᴇ ꜱᴩᴀᴍ ᴋᴀʀɴᴀ ʜ)\n\n"
    "ꜱᴛᴏᴩ ᴄᴍᴅ - .reboot"
)

ONE_WORD_CMD_TEXT = fontify(
    "⚡ ᴏɴᴇ ᴡᴏʀᴅ 1.0\n"
    ".oneraid 10 - ᴏɴᴇ ᴡᴏʀᴅ ʀᴀɪᴅ (ꜱᴩᴇᴇᴅ: 0.2ꜱ)\n"
    ".oneraid ᴛᴇxᴛ - .oneraid + ᴍᴇꜱꜱᴀɢᴇ ᴏɴᴇ ᴡᴏʀᴅ ᴍᴇ ᴊᴀʏᴇɢᴀ\n\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "🔥 ᴏɴᴇ ᴡᴏʀᴅ 2.0 (ꜱᴍᴀʀᴛ ᴛᴀʀɢᴇᴛ)\n"
    "ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ʟɪᴋʜᴏ .auto\n"
    "ꜰɪʀ ᴀᴩɴᴇ ᴛᴀʀɢᴇᴛ ᴋɪ ᴍᴇꜱɢ ʟɪɴᴋ ᴅᴏ ꜰɪʀ ᴀᴩɴᴀ ᴏɴᴇ ᴡᴏʀᴅ ᴍᴇꜱɢ ʟɪᴋʜ ᴅᴇɴᴀ\n\n"
    "ꜱᴛᴏᴩ ᴄᴍᴅ - .stop\n"
    "ʀᴇꜱᴜᴍᴇ ᴄᴍᴅ - .restart"
)

CORE_TOOLS_TEXT = fontify(
    "⚡ ᴄᴏʀᴇ / ᴛᴏᴏʟꜱ\n\n"
    ".ping - ᴩɪɴɢ ꜱᴩᴇᴇᴅᴏᴍᴇᴛᴇʀ (ᴜʟᴛʀᴀ ꜰᴀꜱᴛ)\n"
    ".alive - ᴏɴʟɪɴᴇ ꜱᴛᴀᴛᴜꜱ\n"
    ".uptime - ᴄᴏʀᴇ ᴜᴩᴛɪᴍᴇ\n"
    ".purge [count] - ʙᴜʟᴋ ᴍᴇꜱꜱᴀɢᴇ ᴄʟᴇᴀɴᴇʀ\n"
    ".afk [reason] - ꜱᴍᴀʀᴛ ᴏꜰꜰʟɪɴᴇ ᴍᴏᴅᴇ\n"
    ".timebio on/off - ʟɪᴠᴇ ɪꜱᴛ ᴄʟᴏᴄᴋ ʙɪᴏ\n"
    ".tts [text] - ᴛᴇxᴛ ᴛᴏ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ\n"
    ".logout - ʟᴏɢ ᴏᴜᴛ ᴜꜱᴇʀʙᴏᴛ\n"
    ".help - ᴛʜɪꜱ ᴍᴇɴᴜ"
)

HELP_TEXT = f"""{header()}

🔥 RAID & SPAM
.raid [count]       Reply pe fast raid
.mraid              Reply + Mention raid
.sraid              Ultra fast raid
.rraid              Continuous reply raid
.drraid             Stop reply raid
.oneraid [count/txt] One word raid 1.0 (0.2s speed)
.auto / .stop       One word raid 2.0 (Smart Link)
.spam [count] [txt] Spam messages (0.3s speed)
.reboot             Stop all raids/spam

⚡ SPECIAL COMMANDS (BETA ONLY)
[Target reply] teri maa di fudi
[Target reply] [name] teri maa di fudi
[Target reply] oye chamar uth
[Target reply] [name] chamar uth
.sspam [count] [txt] Ultra fast spam
.speed [seconds]    Special raid delay (Save Msg)
.reboot             Stop all active raids

🎭 UNIQUE FUN & ANIMATIONS
.train              Moving ASCII Steam Train Engine
.gadi / .car        Sports Car High Speed Drift
.rocket / .launch   Space Rocket Blast-off
.scan / .hack       Terminal cyber hacking animation
.glitch [text]      Zalgo corrupted demonic text
.matrix             Digital binary code stream
.bomb               Ticking countdown time-bomb
.loading [text]     Futuristic progress cyber bar
.heart              Pulsing neon rainbow hearts
.flip [text]        Inverted upside-down text

{CORE_TOOLS_TEXT}

🔇 SILENT TOOLS
.chup               Mute replied user (Silent)
.chup all           Mute full group (Silent)
.bol                Unmute replied user (Silent)
.bol all            Unmute full group (Silent)
.cleaning on/off    Full group message wiper

🧬 CLONE ENGINE
.clone              Reply to clone user profile
.back               Restore original profile

{footer()}"""

FORCE_JOIN_TEXT = fontify(
    "⚠️ ᴩʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!\n"
    "✨ ʏᴏᴜ ᴄᴀɴ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴏɴʟʏ ᴀꜰᴛᴇʀ ᴊᴏɪɴɪɴɢ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ."
)

def build_custom_welcome_message(first_name: str, bot_username: str, bot_display_name: str):
    current_uptime = uptime()
    part1 = (
        "┌────── ˹ ɪɴꜰᴏʀᴍᴀᴛɪᴏɴ ˼─── ⏤‌‌ 🔹\n"
        f"┆◍ ʜєʏ, {first_name}\n"
        f"┆◍ ɪ ᴧϻ {bot_display_name}\n"
        "└──────────────────────•\n\n"
    )
    part2 = "ɪ ᴀᴍ ᴛʜᴇ ꜰᴀꜱᴛᴇꜱᴛ ᴜꜱᴇʀʙᴏᴛ ᴡɪᴛʜ ᴀᴡᴇꜱᴏᴍᴇ ꜰᴇᴀᴛᴜʀᴇꜱ, ᴀᴅᴠᴀɴᴄᴇᴅ ᴛᴏᴏʟꜱ ᴀɴᴅ ᴩᴏᴡᴇʀꜰᴜʟ ᴄᴏᴍᴍᴀɴᴅꜱ,\n\n"
    part3 = (
        f"➥ ᴜᴩᴛɪᴍᴇ: {current_uptime}\n"
        "➥ ꜱᴇʀᴠᴇʀ ꜱᴛᴏʀᴀɢᴇ: 100.0%\n"
        "➥ ᴄᴩᴜ ʟᴏᴀᴅ: 11.2%\n"
        "➥ ʀᴀᴍ ᴄᴏɴꜱᴜᴍᴩᴛɪᴏɴ: 69.7%\n\n"
    )
    powered_by_tag = "𝐆 𝐄 𝚻 𝐎"
    part4 = (
        "•──────────────────────•\n"
        f"⌯ ᴩᴏᴡєʀєᴅ ʙʏ »   {powered_by_tag}\n"
        "•──────────────────────•"
    )

    full_text = part1 + part2 + part3 + part4
    o_p2 = utf16_len(part1)
    l_p2 = utf16_len(part2) - 1
    e_p2 = MessageEntityBlockquote(offset=o_p2, length=l_p2, collapsed=True)

    o_p3 = o_p2 + utf16_len(part2)
    l_p3 = utf16_len(part3) - 1
    e_p3 = MessageEntityBlockquote(offset=o_p3, length=l_p3, collapsed=True)

    target_str = f"ɪ ᴧϻ {bot_display_name}"
    start_idx = full_text.find(target_str)
    bot_name_offset = utf16_len(full_text[:start_idx]) + utf16_len("ɪ ᴧϻ ")
    bot_name_len = utf16_len(bot_display_name)
    e_bot_mention = MessageEntityTextUrl(offset=bot_name_offset, length=bot_name_len, url=f"https://t.me/{bot_username}")

    ashish_pos = full_text.find(powered_by_tag, o_p3 + utf16_len(part3))
    ashish_offset = utf16_len(full_text[:ashish_pos])
    ashish_len = utf16_len(powered_by_tag)
    e_link = MessageEntityTextUrl(offset=ashish_offset, length=ashish_len, url=f"https://t.me/{OWNER_USERNAME}")

    return full_text, [e_p2, e_p3, e_bot_mention, e_link]

# ============================================================
#               FORCE JOIN & BOT INTERFACES
# ============================================================

async def is_subscribed(user_id: int) -> bool:
    try:
        await bot.get_permissions(FORCE_CHANNEL, user_id)
        return True
    except UserNotParticipantError:
        return False
    except Exception:
        return True

async def send_welcome_display(chat_id, first_name):
    try:
        bot_username = CACHED_BOT_INFO["username"]
        bot_display_name = CACHED_BOT_INFO["display_name"]
        full_text, entities = build_custom_welcome_message(first_name, bot_username, bot_display_name)
        
        target_path = CACHED_MEDIA.get("path")
        if target_path and os.path.exists(target_path):
            try:
                await bot.send_file(
                    chat_id,
                    file=target_path,
                    caption=full_text,
                    formatting_entities=entities,
                    buttons=start_buttons()
                )
                return
            except Exception:
                pass

        await bot.send_message(
            chat_id,
            full_text,
            formatting_entities=entities,
            buttons=start_buttons(),
            link_preview=False
        )
    except Exception as e:
        await send_error_log(e, context="send_welcome_display")

@bot.on(events.NewMessage(pattern=r"^/start"))
async def start_handler(event):
    try:
        uid = event.sender_id
        if event.is_private:
            try:
                await bot_users_col.update_one(
                    {"user_id": int(uid)}, 
                    {"$set": {"user_id": int(uid), "date": datetime.now()}}, 
                    upsert=True
                )
            except Exception as e:
                await send_error_log(e, context="start_handler - MongoDB User Save")

        sender = await event.get_sender()
        first = sender.first_name if sender and sender.first_name else "User"
        await send_welcome_display(event.chat_id, first)
    except Exception as e:
        await send_error_log(e, context="/start Handler")

@bot.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_callback(event):
    try:
        uid = event.sender_id
        if await is_subscribed(uid):
            await event.answer("✅ ᴠᴇʀɪꜰɪᴇᴅ!", alert=False)
            try:
                await event.delete()
            except Exception:
                pass
            sender = await event.get_sender()
            first = sender.first_name if sender and sender.first_name else "User"
            await send_welcome_display(event.chat_id, first)
        else:
            await event.answer("❌ ᴀᴀᴩɴᴇ ᴀʙʜɪ ᴛᴀᴋ ᴄʜᴀɴɴᴇʟ ᴊᴏɪɴ ɴᴀʜɪ ᴋɪʏᴀ!", alert=True)
    except Exception as e:
        await send_error_log(e, context="check_joined_callback")

# ----------------- ADMIN, STATUS & BETA COMMANDS -----------------

@bot.on(events.NewMessage(pattern=r"^/status$"))
async def bot_status_cmd(event):
    if int(event.sender_id) != int(OWNER_ID):
        return
    try:
        total_started_users = await bot_users_col.count_documents({})
        total_logins = await sessions_col.count_documents({})
        total_active_clients = len(active_clients)
        total_admins = await admins_col.count_documents({})
        total_beta = await beta_users_col.count_documents({})

        active_raids_count = sum(len(v) for v in active_raids.values())
        active_rraids_count = sum(len(v) for v in active_reply_raids.values())
        active_special_raids_count = sum(len(v) for v in active_special_raids.values())
        total_running_attacks = active_raids_count + active_rraids_count + active_special_raids_count

        status_text = (
            "📊 ╭──「 𝐆𝐄𝐓𝐎 𝐗 𝐇𝐎𝐒𝐓𝐄𝐑 • 𝐒𝐓𝐀𝐓𝐔𝐒 」──╮\n"
            "│\n"
            f"├── 👑 ⇒ 𝐎ᴡɴᴇʀ : {MASTER}\n"
            f"├── ⏱ ⇒ 𝐔ᴩᴛɪᴍᴇ : {uptime()}\n"
            f"├── 🌐 ⇒ 𝐒ᴇʀᴠᴇʀ 𝐒ᴛᴀᴛᴜꜱ : ⚡ 𝐎ɴʟɪɴᴇ & 𝐅ᴀꜱᴛ\n"
            "│\n"
            f"├── 👥 ⇒ 𝐓ᴏᴛᴀʟ 𝐒ᴛᴀʀᴛ 𝐔ꜱᴇʀꜱ : `{total_started_users}`\n"
            f"├── 🔐 ⇒ 𝐓ᴏᴛᴀʟ 𝐋ᴏɢɪɴ 𝐔ꜱᴇʀʙᴏᴛꜱ : `{total_logins}`\n"
            f"├── 🟢 ⇒ 𝐀ᴄᴛɪᴠᴇ 𝐔ꜱᴇʀʙᴏᴛ 𝐍ᴏᴅᴇꜱ : `{total_active_clients}`\n"
            f"├── 🛡️ ⇒ 𝐏ʀᴏᴛᴇᴄᴛᴇᴅ 𝐀ᴅᴍɪɴꜱ : `{total_admins}`\n"
            f"├── 🧪 ⇒ 𝐒ᴩᴇᴄɪᴀʟ 𝐁ᴇᴛᴀ 𝐔ꜱᴇʀꜱ : `{total_beta}`\n"
            "│\n"
            f"├── ⚔️ ⇒ 𝐑ᴜɴɴɪɴɢ 𝐀ᴛᴛᴀᴄᴋꜱ : `{total_running_attacks}`\n"
            f"├── 🕒 ⇒ 𝐋ᴀꜱᴛ 𝐑ᴇ-ᴄʜᴇᴄᴋ : {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
            "│\n"
            "╰──────────────────────────────────────────╯"
        )

        styled_text = fontify(status_text)
        await event.respond(
            styled_text,
            formatting_entities=[quote_entity(styled_text, collapsed=False)],
            link_preview=False
        )
    except Exception as e:
        await send_error_log(e, context="/status Command")

@bot.on(events.NewMessage(pattern=r"^/add_admin(?: (.+))?"))
async def add_admin_cmd(event):
    try:
        if int(event.sender_id) != int(OWNER_ID):
            return
        args = event.pattern_match.group(1)
        target_id = None
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            target_id = reply.sender_id
        elif args and args.strip().isdigit():
            target_id = int(args.strip())
        
        if not target_id:
            msg = "⚠️ ᴜꜱᴀɢᴇ: `/add_admin <user_id>`"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        await admins_col.update_one(
            {"user_id": int(target_id)},
            {"$set": {"user_id": int(target_id), "added_at": datetime.now()}},
            upsert=True
        )
        msg = f"✅ ᴜꜱᴇʀ `{target_id}` ᴋᴏ ᴀᴅᴍɪɴ/ᴩʀᴏᴛᴇᴄᴛɪᴏɴ ᴀᴄᴄᴇꜱꜱ ᴅɪʏᴀ ɢᴀʏᴀ!"
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/add_admin")

@bot.on(events.NewMessage(pattern=r"^/rem_admin(?: (.+))?"))
async def rem_admin_cmd(event):
    try:
        if int(event.sender_id) != int(OWNER_ID):
            return
        args = event.pattern_match.group(1)
        target_id = None
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            target_id = reply.sender_id
        elif args and args.strip().isdigit():
            target_id = int(args.strip())

        if not target_id:
            msg = "⚠️ ᴜꜱᴀɢᴇ: `/rem_admin <user_id>`"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        await admins_col.delete_one({"user_id": int(target_id)})
        msg = f"🛑 ᴜꜱᴇʀ `{target_id}` ᴋᴀ ᴀᴅᴍɪɴ ᴀᴄᴄᴇꜱꜱ ʜᴀᴛᴀ ᴅɪʏᴀ ɢᴀʏᴀ!"
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/rem_admin")

@bot.on(events.NewMessage(pattern=r"^/add_beta(?: (.+))?"))
async def add_beta_cmd(event):
    try:
        if int(event.sender_id) != int(OWNER_ID):
            return
        args = event.pattern_match.group(1)
        target_id = None
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            target_id = reply.sender_id
        elif args and args.strip().isdigit():
            target_id = int(args.strip())
        
        if not target_id:
            msg = "⚠️ ᴜꜱᴀɢᴇ: `/add_beta <user_id>`"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        await beta_users_col.update_one(
            {"user_id": int(target_id)},
            {"$set": {"user_id": int(target_id), "added_at": datetime.now()}},
            upsert=True
        )
        msg = f"✅ ᴜꜱᴇʀ `{target_id}` ᴋᴏ ꜱᴩᴇᴄɪᴀʟ ʙᴇᴛᴀ ᴀᴄᴄᴇꜱꜱ ᴅᴇ ᴅɪʏᴀ ɢᴀʏᴀ ʜᴀɪ!"
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/add_beta")

@bot.on(events.NewMessage(pattern=r"^/rem_beta(?: (.+))?"))
async def rem_beta_cmd(event):
    try:
        if int(event.sender_id) != int(OWNER_ID):
            return
        args = event.pattern_match.group(1)
        target_id = None
        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            target_id = reply.sender_id
        elif args and args.strip().isdigit():
            target_id = int(args.strip())

        if not target_id:
            msg = "⚠️ ᴜꜱᴀɢᴇ: `/rem_beta <user_id>`"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        await beta_users_col.delete_one({"user_id": int(target_id)})
        msg = f"🛑 ᴜꜱᴇʀ `{target_id}` ᴋᴀ ꜱᴩᴇᴄɪᴀʟ ʙᴇᴛᴀ ᴀᴄᴄᴇꜱꜱ ʜᴀᴛᴀ ᴅɪʏᴀ ɢᴀʏᴀ!"
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/rem_beta")

@bot.on(events.NewMessage(pattern=r"^/add_message$"))
async def add_special_message(event):
    try:
        if int(event.sender_id) != int(OWNER_ID):
            msg = "❌ ꜱɪʀꜰ ᴏᴡɴᴇʀ ʜɪ ᴍᴇꜱꜱᴀɢᴇꜱ ᴀᴅᴅ ᴋᴀʀ ꜱᴀᴋᴛᴀ ʜᴀɪ!"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return
        reply = await event.get_reply_message()
        if not reply:
            msg = "⚠️ ᴋɪꜱɪ ᴩᴀʀᴀɢʀᴀᴩʜ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/add_message` ʟɪᴋʜᴇɪɴ."
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        raw_text = reply.text or reply.message or ""
        lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
        if not lines:
            msg = "⚠️ ɪꜱ ᴍᴇꜱꜱᴀɢᴇ ᴍᴇ ᴋᴏɪ ʟɪɴᴇꜱ ɴᴀʜɪ ᴍɪʟɪ!"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
            return

        last_doc = await special_msgs_col.find_one(sort=[("line_num", -1)])
        start_num = (last_doc["line_num"] + 1) if (last_doc and "line_num" in last_doc) else 1

        count = 0
        for idx, l in enumerate(lines):
            current_num = start_num + idx
            try:
                await special_msgs_col.update_one(
                    {"line_num": current_num},
                    {"$set": {"line_num": current_num, "text": l, "added_at": datetime.now()}},
                    upsert=True
                )
                count += 1
            except Exception as e:
                await send_error_log(e, context="MongoDB Message Insert")

        msg = f"✅ ᴛᴏᴛᴀʟ {count} ꜱᴩᴇᴄɪᴀʟ ᴍᴇꜱꜱᴀɢᴇꜱ ꜱᴀᴠᴇ ʜᴏ ɢᴀʏᴇ! (ʟɪɴᴇꜱ: {start_num} ꜱᴇ {start_num + count - 1})"
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/add_message")

@bot.on(events.NewMessage(pattern=r"^/setphoto$"))
async def setphoto_handler(event):
    if int(event.sender_id) != int(OWNER_ID):
        return
    reply = await event.get_reply_message()
    if not reply or not reply.photo:
        msg = "⚠️ ᴋɪꜱɪ ᴩʜᴏᴛᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setphoto` ʟɪᴋʜᴏ."
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
        return

    st_msg = "⏳ ꜱᴀᴠɪɴɢ ᴩʜᴏᴛᴏ ᴛᴏ ᴅᴀᴛᴀʙᴀꜱᴇ..."
    status = await event.respond(fontify(st_msg), formatting_entities=[quote_entity(fontify(st_msg), collapsed=False)])
    try:
        await reply.download_media(file=PHOTO_CACHE_PATH)
        if os.path.exists(VIDEO_CACHE_PATH):
            os.remove(VIDEO_CACHE_PATH)

        with open(PHOTO_CACHE_PATH, "rb") as f:
            photo_data = f.read()

        CACHED_MEDIA["type"] = "photo"
        CACHED_MEDIA["path"] = PHOTO_CACHE_PATH

        await settings_col.update_one(
            {"key": "welcome_media_data"},
            {"$set": {"key": "welcome_media_data", "type": "photo", "data": photo_data}},
            upsert=True
        )
        fin_msg = "✅ ᴡᴇʟᴄᴏᴍᴇ ᴩʜᴏᴛᴏ ᴜᴩᴅᴀᴛᴇᴅ & ᴩᴇʀᴍᴀɴᴇɴᴛʟʏ ꜱᴀᴠᴇᴅ!"
        await status.edit(fontify(fin_msg), formatting_entities=[quote_entity(fontify(fin_msg), collapsed=False)])
    except Exception as e:
        err_msg = f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴩʜᴏᴛᴏ: `{e}`"
        await status.edit(fontify(err_msg), formatting_entities=[quote_entity(fontify(err_msg), collapsed=False)])
        await send_error_log(e, context="/setphoto")

@bot.on(events.NewMessage(pattern=r"^/setvideo$"))
async def setvideo_handler(event):
    if int(event.sender_id) != int(OWNER_ID):
        return
    reply = await event.get_reply_message()
    is_video = False
    if reply and reply.media:
        if getattr(reply, 'video', None):
            is_video = True
        elif getattr(reply, 'document', None) and reply.document.mime_type.startswith("video/"):
            is_video = True

    if not is_video:
        msg = "⚠️ ᴋɪꜱɪ ᴠɪᴅᴇᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setvideo` ʟɪᴋʜᴏ."
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
        return

    st_msg = "⏳ ꜱᴀᴠɪɴɢ ᴠɪᴅᴇᴏ ᴛᴏ ᴅᴀᴛᴀʙᴀꜱᴇ..."
    status = await event.respond(fontify(st_msg), formatting_entities=[quote_entity(fontify(st_msg), collapsed=False)])
    try:
        await reply.download_media(file=VIDEO_CACHE_PATH)
        if os.path.exists(PHOTO_CACHE_PATH):
            os.remove(PHOTO_CACHE_PATH)

        with open(VIDEO_CACHE_PATH, "rb") as f:
            video_data = f.read()

        CACHED_MEDIA["type"] = "video"
        CACHED_MEDIA["path"] = VIDEO_CACHE_PATH

        await settings_col.update_one(
            {"key": "welcome_media_data"},
            {"$set": {"key": "welcome_media_data", "type": "video", "data": video_data}},
            upsert=True
        )
        fin_msg = "✅ ᴡᴇʟᴄᴏᴍᴇ ᴠɪᴅᴇᴏ ᴜᴩᴅᴀᴛᴇᴅ & ᴩᴇʀᴍᴀɴᴇɴᴛʟʏ ꜱᴀᴠᴇᴅ!"
        await status.edit(fontify(fin_msg), formatting_entities=[quote_entity(fontify(fin_msg), collapsed=False)])
    except Exception as e:
        err_msg = f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴠɪᴅᴇᴏ: `{e}`"
        await status.edit(fontify(err_msg), formatting_entities=[quote_entity(fontify(err_msg), collapsed=False)])
        await send_error_log(e, context="/setvideo")

@bot.on(events.CallbackQuery(data=b"back_start"))
async def callback_back_start(event):
    try:
        await event.answer()
        sender = await event.get_sender()
        first = sender.first_name if sender and sender.first_name else "User"
        try:
            await event.delete()
        except Exception:
            pass
        await send_welcome_display(event.chat_id, first)
    except Exception as e:
        await send_error_log(e, context="back_start_callback")

@bot.on(events.NewMessage(pattern=r"^/help$"))
async def bot_help_cmd(event):
    try:
        if not await is_subscribed(event.sender_id):
            await event.respond(
                FORCE_JOIN_TEXT,
                formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
                buttons=force_join_buttons()
            )
            return
        styled_help = fontify(HELP_TEXT)
        entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_help), collapsed=True)
        back_btn = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"back_start")]]
        await event.respond(styled_help, formatting_entities=[entity], buttons=back_btn)
    except Exception as e:
        await send_error_log(e, context="/help")

# ============================================================
#             COMMAND CENTER & MENUS
# ============================================================

@bot.on(events.CallbackQuery(data=b"open_help_guide"))
async def open_help_guide_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"back_start")]]
    await safe_edit_card(event, HELP_GUIDE_TEXT, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"menu_help_cats"))
async def menu_help_cats_cb(event):
    await event.answer()
    buttons = [
        [
            safe_button("inline", "「 ᴩʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"pro_cmds_menu"),
            safe_button("inline", "「 ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"advance_cmds_menu")
        ],
        [
            safe_button("inline", "「 ꜱᴩᴇᴄɪᴀʟ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"special_cmds_menu"),
            safe_button("inline", "「 🎭 ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"fun_cmds_menu")
        ],
        [safe_button("inline", "「 ʙᴀᴄᴋ 」", b"back_start")]
    ]
    await safe_edit_card(event, CMD_CENTER_TEXT, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"fun_cmds_menu"))
async def fun_cmds_menu_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"menu_help_cats")]]
    await safe_edit_card(event, FUN_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"special_cmds_menu"))
async def special_cmds_menu_cb(event):
    user_id = event.sender_id
    if not await is_beta_user(user_id):
        non_beta_alert = "ᴊᴀᴀ ʙᴇᴛᴀ ᴩᴇʟᴇ ᴀꜱʜɪꜱʜ ᴋᴏ ʙᴀᴀᴩ ʙᴏʟ ᴋᴇ ᴀᴀ ꜰɪʀ ᴡᴏ ᴅᴇɢᴀ ꜱᴩᴇᴄɪᴀʟ ᴄᴍᴅꜱ ᴋᴀ ᴀᴄᴄᴇꜱꜱ"
        await event.answer(non_beta_alert, alert=True)
        return

    await event.answer()
    buttons = [
        [safe_button("inline", "「 ʀᴀɪᴅ 」", b"sp_info_raid"), safe_button("inline", "「 ʀᴇᴩʟʏ ʀᴀɪᴅ 」", b"sp_info_rraid")],
        [safe_button("inline", "「 .ʀᴇʙᴏᴏᴛ 」", b"sp_info_reboot")],
        [safe_button("inline", "「 ꜱᴩᴀᴍ 」", b"sp_info_spam"), safe_button("inline", "「 ᴏɴᴇ ᴡᴏʀᴅ 」", b"sp_info_oneword")],
        [safe_button("inline", "「 ʙᴀᴄᴋ 」", b"menu_help_cats")]
    ]
    await safe_edit_card(event, SPECIAL_CMD_HEADER_TEXT, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"sp_info_raid"))
async def sp_info_raid_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_RAID_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_rraid"))
async def sp_info_rraid_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_RRAID_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_reboot"))
async def sp_info_reboot_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_REBOOT_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_oneword"))
async def sp_info_oneword_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_ONEWORD_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_spam"))
async def sp_info_spam_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_SPAM_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"advance_cmds_menu"))
async def advance_cmds_menu_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"menu_help_cats")]]
    await safe_edit_card(event, ADVANCE_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"pro_cmds_menu"))
async def pro_cmds_menu_cb(event):
    await event.answer()
    buttons = [
        [safe_button("inline", "「 ʀᴀɪᴅ 」", b"info_raid"), safe_button("inline", "「 ʀᴇᴩʟʏ ʀᴀɪᴅ 」", b"info_rraid")],
        [safe_button("inline", "「 ꜱᴩᴀᴍ 」", b"info_spam"), safe_button("inline", "「 ᴏɴᴇ ᴡᴏʀᴅ 」", b"info_oneraid")],
        [safe_button("inline", "「 ᴄʟᴏɴᴇ 」", b"info_clone"), safe_button("inline", "「 ᴄʜᴜᴩ 」", b"info_chup")],
        [safe_button("inline", "「 ᴄʜᴜᴩ ᴀʟʟ 」", b"info_chup_all"), safe_button("inline", "「 ᴄʟᴇᴀɴɪɴɢ 」", b"info_cleaning")],
        [safe_button("inline", "「 ʙᴀᴄᴋ 」", b"menu_help_cats")]
    ]
    await safe_edit_card(event, PRO_CMD_WELCOME, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"info_raid"))
async def info_raid_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, RAID_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_rraid"))
async def info_rraid_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, REPLY_RAID_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_spam"))
async def info_spam_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, SPAM_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_oneraid"))
async def info_oneraid_cb(event):
    await event.answer()
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, ONE_WORD_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_clone"))
async def info_clone_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʟᴏɴᴇ -  .clone ᴋɪꜱɪ ʙʜɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ʀᴇᴩʟʏ ᴅᴇ ᴋᴇ .clone ʟɪᴋʜᴏ\n\n"
        "ᴄʟᴏɴᴇ ʜᴀᴛᴀɴᴇ ᴋᴇ ʟɪʏᴇ: .back"
    )
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_chup"))
async def info_chup_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʜᴜᴩ - .chup ᴋɪꜱɪ ʙʜɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴇ ʀᴇᴩʟʏ ᴅᴇ ᴋᴇ ʟɪᴋʜᴏ\n\n"
        ".bol - ɪꜱ ꜱᴇ ᴡᴏ ᴜɴᴍᴜᴛᴇ ʜᴏ ᴊᴀʏᴇɢᴀ"
    )
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_chup_all"))
async def info_chup_all_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʜᴜᴩ ᴀʟʟ - .chup all ꜱᴇ ɢᴄ ᴍᴜᴛᴇ ʜᴏɢɪ\n\n"
        ".bol all - ᴜɴᴍᴜᴛᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ"
    )
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_cleaning"))
async def info_cleaning_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʟᴇᴀɴɪɴɢ - .cleaning on ꜱᴇ ɢᴄ ꜱᴀꜰᴀɪ ꜱᴛᴀʀᴛ ʜᴏɢɪ\n\n"
        ".cleaning off - ɪꜱ ꜱᴇ ꜱᴀꜰᴀɪ ʀᴜᴋ ᴊᴀʏᴇɢɪ"
    )
    buttons = [[safe_button("inline", "「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

# ============================================================
#                 LOGIN & LOGOUT HANDLERS
# ============================================================

@bot.on(events.NewMessage(pattern=r"^/logout$"))
async def cmd_logout(event):
    try:
        uid = event.sender_id
        if uid in active_clients:
            await perform_logout(uid)
            msg = "🚪 ᴀᴀᴩᴋᴀ ᴜꜱᴇʀʙᴏᴛ ꜱᴇꜱꜱɪᴏɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇ ᴀᴜʀ ᴅᴇʟᴇᴛᴇ ʜᴏ ɢᴀʏᴀ!"
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
        else:
            msg = "⚠️ ᴀᴀᴩᴋᴀ ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ᴜꜱᴇʀʙᴏᴛ ʟᴏɢɪɴ ɴᴀʜɪ ᴍɪʟᴀ."
            await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/logout")

@bot.on(events.CallbackQuery(data=b"start_login"))
async def start_login_callback(event):
    try:
        if not await is_subscribed(event.sender_id):
            await event.answer("⚠️ ᴩᴇʜʟᴇ ᴄʜᴀɴɴᴇʟ ᴊᴏɪɴ ᴋᴀʀᴇɪɴ!", alert=True)
            await event.respond(
                FORCE_JOIN_TEXT,
                formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
                buttons=force_join_buttons()
            )
            return
        await event.answer()
        await start_login_flow(event.chat_id, event.sender_id)
    except AlreadyInConversationError:
        await event.answer("⚠️ ᴇᴋ ʟᴏɢɪɴ ᴩʀᴏᴄᴇꜱꜱ ᴩᴇʜʟᴇ ꜱᴇ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴀɪ!", alert=True)
    except Exception as e:
        await send_error_log(e, context="start_login_callback")

@bot.on(events.NewMessage(pattern=r"^/add$"))
async def add_cmd_handler(event):
    try:
        if not await is_subscribed(event.sender_id):
            await event.respond(
                FORCE_JOIN_TEXT,
                formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
                buttons=force_join_buttons()
            )
            return
        await start_login_flow(event.chat_id, event.sender_id)
    except AlreadyInConversationError:
        msg = "⚠️ ᴇᴋ ʟᴏɢɪɴ ᴩʀᴏᴄᴇꜱꜱ ᴩᴇʜʟᴇ ꜱᴇ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴀɪ! ᴋʀɪᴩʏᴀ ᴛʜᴏᴅᴀ ɪɴᴛᴇᴢᴀᴀʀ ᴋᴀʀᴇɪɴ."
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
    except Exception as e:
        await send_error_log(e, context="/add Handler")

# ============================================================
#       🔥 /login <number> - DIRECT TELEGRAM OTP FETCHER 🔥
# ============================================================

@bot.on(events.NewMessage(pattern=r"^/login(?: (.+))?"))
async def login_otp_fetcher(event):
    try:
        # Owner check: Sirf owner hi access kar sakta hai
        if int(event.sender_id) != int(OWNER_ID):
            deny_msg = (
                "⚠️ ╭──「 𝐀ᴄᴄᴇꜱꜱ 𝐃ᴇɴɪᴇᴅ 」──╮\n"
                "│\n"
                "├── 🚫 ⇒ ʏᴇʜ ᴄᴏᴍᴍᴀɴᴅ ꜱɪʀꜰ ᴏᴡɴᴇʀ ᴋᴇ ʟɪʏᴇ ʜᴀɪ!\n"
                "│\n"
                "╰──────────────────────────╯"
            )
            styled_deny = fontify(deny_msg)
            await event.respond(styled_deny, formatting_entities=[quote_entity(styled_deny, collapsed=False)])
            return

        arg = event.pattern_match.group(1)
        if not arg or not arg.strip():
            usage_msg = (
                "⚠️ ╭──「 𝐔ꜱᴀɢᴇ 𝐆ᴜɪᴅᴇ 」──╮\n"
                "│\n"
                "├── 📱 ⇒ /login <phone_number>\n"
                "├── 📌 ⇒ Ex: `/login +919876543210`\n"
                "│\n"
                "╰────────────────────────╯"
            )
            styled_usage = fontify(usage_msg)
            await event.respond(styled_usage, formatting_entities=[quote_entity(styled_usage, collapsed=False)])
            return

        raw_phone = arg.strip().replace(" ", "").replace("-", "")
        phone = raw_phone if raw_phone.startswith("+") else ("+" + raw_phone)

        # Database me check karo ki number bot par actively running hai ya nahi
        session_data = await sessions_col.find_one({"phone": phone})
        if not session_data or session_data.get("user_id") not in active_clients:
            err_msg = (
                "❌ ╭──「 𝐀ᴄᴄᴏᴜɴᴛ 𝐍ᴏᴛ 𝐅ᴏᴜɴᴅ 」──╮\n"
                "│\n"
                f"├── 📱 ⇒ `{phone}` ʙᴏᴛ ᴩᴀʀ ᴀᴄᴛɪᴠᴇ ɴᴀʜɪ ʜᴀɪ!\n"
                "├── ⚠️ ⇒ ᴩᴇʜʟᴇ ɪꜱ ɴᴜᴍʙᴇʀ ᴋᴏ /add ꜱᴇ ʙᴏᴛ ᴍᴇ ʟᴏɢɪɴ ᴋᴀʀᴏ.\n"
                "│\n"
                "╰─────────────────────────────╯"
            )
            styled_err = fontify(err_msg)
            await event.respond(styled_err, formatting_entities=[quote_entity(styled_err, collapsed=False)])
            return

        target_client = active_clients[session_data["user_id"]]

        # 777000 (Telegram Service Notifications) se latest OTP messages check karo
        try:
            messages = await target_client.get_messages(777000, limit=3)
            if not messages:
                no_msg = f"⚠️ `{phone}` ᴋᴇ ᴛᴇʟᴇɢʀᴀᴍ ꜱᴇʀᴠɪᴄᴇ (777000) ᴍᴇ ᴋᴏɪ ᴍᴇꜱꜱᴀɢᴇ ɴᴀʜɪ ᴍɪʟᴀ."
                styled_no = fontify(no_msg)
                await event.respond(styled_no, formatting_entities=[quote_entity(styled_no, collapsed=False)])
                return

            latest_text = messages[0].message or ""

            # Telegram OTP nikalna (digits match)
            otp_match = re.search(r"\b(\d{5,6})\b", latest_text)
            if not otp_match:
                otp_match = re.search(r"\b(\d{4,7})\b", latest_text)

            if otp_match:
                raw_code = otp_match.group(1)
                spaced_otp = " ".join(list(raw_code))
            else:
                spaced_otp = "OTP detect nahi hua"

            # Clean card format (Requested spaced OTP representation)
            otp_card = (
                "🔑 ╭──「 𝐓ᴇʟᴇɢʀᴀᴍ 𝐋ᴏɢɪɴ 𝐎ᴛᴩ 」──╮\n"
                "│\n"
                f"├── 📱 ⇒ 𝐏ʜᴏɴᴇ: `{phone}`\n"
                f"├── ⚡ ⇒ 𝐎ᴛᴩ 𝐂ᴏᴅᴇ: `{spaced_otp}`\n"
                "│\n"
                f"├── 📩 ⇒ 𝐑ᴀᴡ 𝐓ᴇxᴛ:\n"
                f"│   `{latest_text[:140]}...`\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            styled_card = fontify(otp_card)

            # 1. User/Owner ke chat me bhejo
            await event.respond(styled_card, formatting_entities=[quote_entity(styled_card, collapsed=False)])

            # 2. Logger GC me notification bhejo
            asyncio.create_task(log_to_channel(styled_card))

        except Exception as e:
            await send_error_log(e, context="login_otp_fetcher (777000 fetch)")
            await event.respond(f"❌ Error reading OTP: `{e}`")

    except Exception as e:
        await send_error_log(e, context="/login Handler")

async def start_login_flow(chat_id, user_id):
    login_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await login_client.connect()

    try:
        async with bot.conversation(chat_id, timeout=300) as conv:
            panel_card = (
                "🩸 ╭──「 𝐒ᴇᴄᴜʀᴇ 𝐋ᴏɢɪɴ 𝐏ᴀɴᴇʟ 」──╮\n"
                "│\n"
                "├── 💍 ⇒ 𝐒ᴇɴᴅ 𝐘ᴏᴜʀ 𝐏ʜᴏɴᴇ 𝐍ᴜᴍʙᴇʀ\n"
                "│   ⇒ +91XXXXXXXXXX\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            styled_panel = fontify(panel_card)
            await conv.send_message(styled_panel, formatting_entities=[quote_entity(styled_panel, collapsed=False)])
            phone_msg = await conv.get_response()
            raw_phone = phone_msg.text.strip().replace(" ", "").replace("-", "")
            phone = raw_phone if raw_phone.startswith("+") else ("+" + raw_phone)

            try:
                sent_code = await login_client.send_code_request(phone)
            except PhoneNumberInvalidError:
                err_box = fontify("❌ [ LOGIN FAILED ]\n\n⇒ ɪɴᴠᴀʟɪᴅ ᴩʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴇɴᴛᴇʀᴇᴅ! ᴄʜᴇᴄᴋ ꜰᴏʀᴍᴀᴛ (+91...).")
                await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
                await login_client.disconnect()
                return
            except PhoneNumberBannedError:
                err_box = fontify("❌ [ LOGIN FAILED ]\n\n⇒ ʏᴇʜ ɴᴜᴍʙᴇʀ ᴛᴇʟᴇɢʀᴀᴍ ᴩᴀʀ ʙᴀɴɴᴇᴅ ʜᴀɪ!")
                await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
                await login_client.disconnect()
                return
            except FloodWaitError as fwe:
                err_box = fontify(f"❌ [ RATE LIMITED ]\n\n⇒ ᴛᴇʟᴇɢʀᴀᴍ ʟɪᴍɪᴛ: ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ `{fwe.seconds}` ꜱᴇᴄᴏɴᴅꜱ.")
                await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
                await login_client.disconnect()
                return
            except Exception as e:
                err_box = fontify(f"❌ [ LOGIN FAILED ]\n\n⇒ Error: {e}")
                await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
                await login_client.disconnect()
                await send_error_log(e, context="start_login_flow (send_code_request)")
                return

            otp_card = (
                "🩸 ╭──「 𝐎ᴛᴩ 𝐕ᴇʀɪꜰɪᴄᴀᴛɪᴏɴ 」──╮\n"
                "│\n"
                f"├── 🪄 ⇒ 𝐎ᴛᴩ 𝐒ᴇɴᴛ 𝐓ᴏ {phone}\n"
                "│   ⇒ 𝐒ᴇɴᴅ 𝐎ᴛᴩ 𝐖ɪᴛʜ 𝐒ᴩᴀᴄᴇꜱ (𝐄x: 𝟣 𝟤 𝟛 𝟜 𝟝)\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            styled_otp = fontify(otp_card)
            await conv.send_message(styled_otp, formatting_entities=[quote_entity(styled_otp, collapsed=False)])
            otp_msg = await conv.get_response()
            otp = re.sub(r"\D", "", otp_msg.text.strip())

            try:
                await login_client.sign_in(phone, code=otp, phone_code_hash=sent_code.phone_code_hash)
            except SessionPasswordNeededError:
                pw_card = (
                    "🩸 ╭── [ 2ꜰᴀ ꜱᴇᴄᴜʀɪᴛʏ ʟᴏᴄᴋ ] ]\n"
                    "│\n"
                    "├── 🔐 ⇒ ᴇɴᴛᴇʀ ʏᴏᴜʀ 2ꜰᴀ ᴩᴀꜱꜱᴡᴏʀᴅ\n"
                    "└──"
                )
                styled_pw = fontify(pw_card)
                await conv.send_message(styled_pw, formatting_entities=[quote_entity(styled_pw, collapsed=False)])
                pw_msg = await conv.get_response()
                try:
                    await login_client.sign_in(password=pw_msg.text.strip())
                except PasswordHashInvalidError:
                    err_pw = fontify("❌ [ ERROR ]\n\n⇒ ᴡʀᴏɴɢ 2ꜰᴀ ᴩᴀꜱꜱᴡᴏʀᴅ! ꜱᴇꜱꜱɪᴏɴ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ.")
                    await conv.send_message(err_pw, formatting_entities=[quote_entity(err_pw, collapsed=False)])
                    await login_client.disconnect()
                    return
            except PhoneCodeInvalidError:
                err_code = fontify("❌ [ ERROR ]\n\n⇒ ɪɴᴠᴀʟɪᴅ ᴏᴛᴩ ᴇɴᴛᴇʀᴇᴅ! ꜱᴇꜱꜱɪᴏɴ ᴄᴀɴᴄᴇʟᴇᴅ.")
                await conv.send_message(err_code, formatting_entities=[quote_entity(err_code, collapsed=False)])
                await login_client.disconnect()
                return
            except Exception as e:
                err_sign = fontify(f"❌ [ AUTH ERROR ]\n\n⇒ {e}")
                await conv.send_message(err_sign, formatting_entities=[quote_entity(err_sign, collapsed=False)])
                await login_client.disconnect()
                await send_error_log(e, context="start_login_flow (sign_in)")
                return

            string_session = login_client.session.save()
            await sessions_col.update_one(
                {"user_id": user_id},
                {"$set": {"user_id": user_id, "phone": phone, "session": string_session}},
                upsert=True
            )

            success_card = (
                "🩸 ╭──「 𝐍ᴏᴅᴇ 𝐂ᴏɴɴᴇᴄᴛᴇᴅ 𝐒ᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ 」──╮\n"
                "│\n"
                "├── 💎 ⇒ 𝐒ᴛᴀᴛᴜꜱ: 𝐎ɴʟɪɴᴇ\n"
                "├── 🌟 ⇒ 𝐘ᴏᴜʀ 𝐔ꜱᴇʀʙᴏᴛ ɪꜱ 𝐍ᴏᴡ 𝐀ᴄᴛɪᴠᴇ!\n"
                "├── 🚪 ⇒ 𝐖ᴀɴᴛ 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ?\n"
                "│   ⇒ 𝐔ꜱᴇ /logout 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ 𝐅ʀᴏᴍ 𝐓ʜᴇ 𝐔ꜱᴇʀʙᴏᴛ.\n"
                "│\n"
                "╰────────────────────────────────────╯"
            )
            styled_succ = fontify(success_card)
            await conv.send_message(styled_succ, formatting_entities=[quote_entity(styled_succ, collapsed=False)])

            session_card = (
                "🔐 ╭── [ YOUR STRING SESSION ]\n"
                "│\n"
                f"`{string_session}`\n\n"
                "⚠️ ᴋɪꜱɪ ᴋᴇ ꜱᴀᴀᴛʜ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋᴀʀɴᴀ!\n"
                "└──"
            )
            styled_sess = fontify(session_card)
            await conv.send_message(styled_sess, formatting_entities=[quote_entity(styled_sess, collapsed=False)])

            try:
                await login_client.send_message(
                    "me",
                    f"✨ **GETO X HOSTER • STRING SESSION** ✨\n\n`{string_session}`\n\n⚠️ Keep it safe!"
                )
            except Exception:
                pass

            try:
                me = await login_client.get_me()
                u_name = me.first_name or "Unknown"
                u_handle = f"@{me.username}" if me.username else "None"
                
                logger_text = (
                    "🚀 ╭──「 𝐍ᴇᴡ 𝐔ꜱᴇʀʙᴏᴛ 𝐋ᴏɢɪɴ 」──╮\n"
                    "│\n"
                    f"├── 👤 ⇒ 𝐍ᴀᴍᴇ: {u_name}\n"
                    f"├── 🏷 ⇒ 𝐔ꜱᴇʀɴᴀᴍᴇ: {u_handle}\n"
                    f"├── 🆔 ⇒ 𝐔ꜱᴇʀ ɪ𝐃: `{user_id}`\n"
                    f"├── 📱 ⇒ 𝐏ʜᴏɴᴇ: `{phone}`\n"
                    f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
                    "│\n"
                    "╰────────────────────────────╯"
                )
                asyncio.create_task(log_to_channel(logger_text))
            except Exception as e:
                await send_error_log(e, context="start_login_flow (Logger Dispatch)")

            if user_id in active_clients:
                old_inst = active_clients.pop(user_id)
                try:
                    if old_inst.is_connected():
                        await old_inst.disconnect()
                except Exception:
                    pass

            register_userbot_handlers(login_client, user_id)
            active_clients[user_id] = login_client
            asyncio.create_task(login_client.run_until_disconnected())

    except (TimeoutError, asyncio.TimeoutError):
        try:
            expire_card = (
                "⏱️ ╭──「 𝐒ᴇꜱꜱɪᴏɴ 𝐄xᴩɪʀᴇᴅ 」──╮\n"
                "│\n"
                "├── ⚠️ ⇒ 𝐋ᴏɢɪɴ ꜱᴇꜱꜱɪᴏɴ ᴇxᴩɪʀᴇ ʜᴏ ɢᴀʏᴀ!\n"
                "├── 📌 ⇒ ᴀᴀᴩɴᴇ ꜱᴀᴍᴀʏ ᴩᴀʀ ɴᴜᴍʙᴇʀ ʏᴀ ᴏᴛᴩ ɴᴀʜɪ ʙʜᴇᴊᴀ.\n"
                "├── 🔄 ⇒ ᴅᴏʙᴀʀᴀ ʟᴏɢɪɴ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ /add ᴅᴀʟᴇɪɴ.\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            styled_exp = fontify(expire_card)
            await bot.send_message(
                chat_id,
                styled_exp,
                formatting_entities=[quote_entity(styled_exp, collapsed=False)],
                link_preview=False
            )
        except Exception:
            pass
        if login_client.is_connected():
            await login_client.disconnect()
        return

    except AlreadyInConversationError:
        try:
            already_card = (
                "⚠️ ╭──「 𝐀ʟʀᴇᴀᴅʏ 𝐀ᴄᴛɪᴠᴇ 」──╮\n"
                "│\n"
                "├── ❌ ⇒ ᴇᴋ ʟᴏɢɪɴ ᴩʀᴏᴄᴇꜱꜱ ᴩᴇʜʟᴇ ꜱᴇ ᴄʜᴀʟ ʀᴀʜᴀ ʜᴀɪ!\n"
                "├── ⏳ ⇒ ᴋʀɪᴩʏᴀ ᴜꜱᴇ ᴩᴜʀᴀ ᴋᴀʀᴇɪɴ ʏᴀ ᴋᴜᴄʜ ᴅᴇʀ ʙᴀᴀᴅ ᴛʀʏ ᴋᴀʀᴇɪɴ.\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            styled_alr = fontify(already_card)
            await bot.send_message(
                chat_id,
                styled_alr,
                formatting_entities=[quote_entity(styled_alr, collapsed=False)],
                link_preview=False
            )
        except Exception:
            pass
        if login_client.is_connected():
            await login_client.disconnect()
        return

    except Exception as e:
        if login_client.is_connected():
            await login_client.disconnect()
        await send_error_log(e, context="start_login_flow")

# ============================================================
#             BULLETPROOF BROADCAST ENGINE
# ============================================================

@bot.on(events.NewMessage(pattern=r"^/broadcast(?: (.+))?"))
async def broadcast_handler(event):
    if int(event.sender_id) != int(OWNER_ID):
        return

    reply = await event.get_reply_message()
    custom_text = event.pattern_match.group(1)
    if not reply and not custom_text:
        msg = "⚠️ ᴋɪꜱɪ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/broadcast` ʟɪᴋʜᴏ ʏᴀ `/broadcast <text>` ʙʜᴇᴊᴏ."
        await event.respond(fontify(msg), formatting_entities=[quote_entity(fontify(msg), collapsed=False)])
        return

    st_msg = "🔍 ᴛᴀʀɢᴇᴛꜱ ɢᴀᴛʜᴇʀ ʜᴏ ʀᴀʜᴇ ʜᴀɪɴ..."
    status = await event.respond(fontify(st_msg), formatting_entities=[quote_entity(fontify(st_msg), collapsed=False)])
    target_ids = set()

    try:
        async for doc in bot_users_col.find({}):
            if "user_id" in doc:
                try:
                    target_ids.add(int(doc["user_id"]))
                except Exception:
                    pass

        async for doc in sessions_col.find({}):
            if "user_id" in doc:
                try:
                    target_ids.add(int(doc["user_id"]))
                except Exception:
                    pass
    except Exception as e:
        err_msg = f"❌ Target fetching error: `{e}`"
        await status.edit(fontify(err_msg), formatting_entities=[quote_entity(fontify(err_msg), collapsed=False)])
        await send_error_log(e, context="broadcast_handler - DB Fetch")
        return

    total = len(target_ids)
    if total == 0:
        err_msg = "❌ ᴅᴀᴛᴀʙᴀꜱᴇ ᴍᴇ ᴋᴏɪ ʙʜɪ ᴜꜱᴇʀꜱ ɴᴀʜɪ ᴍɪʟᴇ!"
        await status.edit(fontify(err_msg), formatting_entities=[quote_entity(fontify(err_msg), collapsed=False)])
        return

    start_prog = f"🚀 ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜱᴛᴀʀᴛᴇᴅ!\nᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛꜱ: `{total}`\nᴩʀᴏɢʀᴇꜱꜱ: `0/{total}`"
    await status.edit(fontify(start_prog), formatting_entities=[quote_entity(fontify(start_prog), collapsed=False)])

    success = 0
    failed = 0

    for idx, target in enumerate(target_ids, 1):
        try:
            try:
                peer = await bot.get_input_entity(target)
            except Exception:
                peer = target

            if reply:
                try:
                    await bot.forward_messages(peer, reply)
                except Exception:
                    if reply.text or reply.message:
                        await bot.send_message(peer, reply.text or reply.message)
                    elif reply.media:
                        await bot.send_file(peer, reply.media, caption=reply.message or "")
            else:
                await bot.send_message(peer, custom_text)

            success += 1
            await asyncio.sleep(0.15)
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds + 1)
        except Exception:
            failed += 1

        if idx % 15 == 0:
            try:
                up_prog = f"⏳ ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...\nᴅᴏɴᴇ: `{idx}/{total}`\nꜱᴜᴄᴄᴇꜱꜱ: `{success}`\nꜰᴀɪʟᴇᴅ: `{failed}`"
                await status.edit(fontify(up_prog), formatting_entities=[quote_entity(fontify(up_prog), collapsed=False)])
            except Exception:
                pass

    fin_card = (
        f"✅ ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜰɪɴɪꜱʜᴇᴅ!\n\n"
        f"🎯 ᴅᴇʟɪᴠᴇʀᴇᴅ: `{success}`\n"
        f"❌ ꜰᴀɪʟᴇᴅ / ʙʟᴏᴄᴋᴇᴅ: `{failed}`\n"
        f"📊 ᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛꜱ: `{total}`"
    )
    await status.edit(fontify(fin_card), formatting_entities=[quote_entity(fontify(fin_card), collapsed=False)])

# ============================================================
#             USERBOT COMMANDS (ATTACHED PER CLIENT)
# ============================================================

def register_userbot_handlers(uclient: TelegramClient, owner_uid: int):

    if owner_uid not in active_raids:
        active_raids[owner_uid] = set()
    if owner_uid not in active_reply_raids:
        active_reply_raids[owner_uid] = set()
    if owner_uid not in active_special_raids:
        active_special_raids[owner_uid] = {}
    if owner_uid not in active_special_reply_raids:
        active_special_reply_raids[owner_uid] = {}
    if owner_uid not in user_special_speeds:
        user_special_speeds[owner_uid] = 0.3
    if owner_uid not in auto_user_states:
        auto_user_states[owner_uid] = {}
    if owner_uid not in auto_raid_active:
        auto_raid_active[owner_uid] = False
    if owner_uid not in u_chup_targets:
        u_chup_targets[owner_uid] = {}
    if owner_uid not in u_chup_all:
        u_chup_all[owner_uid] = set()
    if owner_uid not in u_cleaning_chats:
        u_cleaning_chats[owner_uid] = set()

    async def run_smart_auto_raid():
        state = auto_user_states.get(owner_uid, {}).get("current")
        if not state or not state.get("remaining_words"):
            return

        entity = state["entity"]
        target_user_id = state["target_user_id"]
        words = state["remaining_words"]
        initial_msg_id = state.get("initial_msg_id")

        if await is_protected_user(target_user_id):
            auto_user_states[owner_uid].clear()
            auto_raid_active[owner_uid] = False
            await uclient.send_message(entity, PROTECTION_WARNING)
            await send_card(uclient, owner_uid, f"🛡️ [PROTECTION TRIGGERED] Target `{target_user_id}` ek Protected Admin/Owner hai!", collapsed=False)
            return

        auto_raid_active[owner_uid] = True
        start_txt = (
            f"🚀 ᴏɴᴇ ᴡᴏʀᴅ 2.0 ꜱᴛᴀʀᴛᴇᴅ!\n"
            f"ᴛᴀʀɢᴇᴛ ɪᴅ: `{target_user_id}`\n"
            f"ʀᴇᴍᴀɪɴɪɴɢ ᴡᴏʀᴅꜱ: `{len(words)}`\n"
            f"ꜱᴩᴇᴇᴅ: `0.3s`"
        )
        await send_card(uclient, owner_uid, start_txt, collapsed=False)

        while words and auto_raid_active.get(owner_uid, False):
            word = words[0]
            try:
                target_msg_id = await fetch_target_latest_message(uclient, entity, target_user_id, initial_msg_id)
                await uclient.send_message(entity, word, reply_to=target_msg_id)
                words.pop(0)
                await asyncio.sleep(0.3)
            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 1)
            except Exception as e:
                await send_error_log(e, context=f"run_smart_auto_raid (User {owner_uid})")
                auto_raid_active[owner_uid] = False
                break

        auto_raid_active[owner_uid] = False
        if not words:
            auto_user_states[owner_uid].clear()
            await send_card(uclient, owner_uid, "🏁 ᴏɴᴇ ᴡᴏʀᴅ 2.0 ᴄᴏᴍᴩʟᴇᴛᴇ! ꜱᴀᴀʀᴇ ᴡᴏʀᴅꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʙʜᴇᴊ ᴅɪʏᴇ ɢᴀʏᴇ.", collapsed=False)

    async def timebio_loop():
        ist = timezone(timedelta(hours=5, minutes=30))
        while True:
            try:
                now_str = datetime.now(ist).strftime("%I:%M %p")
                bio_text = f"𝚨 𝐒 𝚮 𝚰 𝐒 𝚮 | 🕒 {now_str} IST | Powered by Hoster"
                await uclient(UpdateProfileRequest(about=bio_text))
            except Exception as e:
                await send_error_log(e, context=f"timebio_loop (User {owner_uid})")
            await asyncio.sleep(60)

    # ========== LOGOUT & HELP ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.logout$"))
    async def uclient_logout(event):
        if event.sender_id != owner_uid:
            return
        active_raids[owner_uid].discard(event.chat_id)
        active_special_raids[owner_uid].pop(event.chat_id, None)
        auto_raid_active[owner_uid] = False
        await reply_card(uclient, event, "🚪 ᴜꜱᴇʀʙᴏᴛ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ & ꜱᴇꜱꜱɪᴏɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ꜱᴇʀᴠᴇʀ.", collapsed=False)
        await perform_logout(owner_uid)

    # ========== UPDATED PING ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def ping_cmd(event):
        if event.sender_id != owner_uid:
            return

        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None
            try:
                await event.delete()
            except Exception:
                pass

            me = await uclient.get_me()
            user_mention = f"@{me.username}" if me.username else (me.first_name or "User")

            started = time.perf_counter()

            init_card_text = (
                "╭━〔 𝐆𝐄𝐓𝐎 𝐗 𝐇𝐎𝐒𝐓𝐄𝐑 〕━╮\n"
                "┣ • 𝐒ᴘᴇᴇᴅ   : ▰▱▱▱▱▱▱▱▱\n"
                "┣ • 𝐒ᴛᴀᴛᴜs  : ⚡ 𝐅ᴀsᴛ\n"
                f"┣ • 𝐔ᴘᴛɪᴍᴇ  : {uptime()}\n"
                f"┣ • 𝐎ᴡɴᴇʀ   : {user_mention}\n"
                "╰━━━━━━━━━━━━━━━━━━╯"
            )

            styled_init = fontify(init_card_text).replace(fontify(user_mention), user_mention)
            init_entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_init), collapsed=True)

            msg = await uclient.send_message(
                event.chat_id,
                styled_init,
                reply_to=reply_to_id,
                parse_mode=None,
                formatting_entities=[init_entity],
                link_preview=False
            )

            ping_ms = (time.perf_counter() - started) * 1000

            final_card_text = (
                "╭━〔 𝐆𝐄𝐓𝐎 𝐗 𝐇𝐎𝐒𝐓𝐄𝐑 〕━╮\n"
                f"┣ • 𝐒ᴘᴇᴇᴅ   : {ping_ms:.2f} ms\n"
                "┣ • 𝐒ᴛᴀᴛᴜs  : ⚡ 𝐅ᴀsᴛ\n"
                f"┣ • 𝐔ᴘᴛɪᴍᴇ  : {uptime()}\n"
                f"┣ • 𝐎ᴡɴᴇʀ   : {user_mention}\n"
                "╰━━━━━━━━━━━━━━━━━━╯"
            )

            styled_final = fontify(final_card_text).replace(fontify(user_mention), user_mention)
            final_entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_final), collapsed=True)

            await msg.edit(styled_final, formatting_entities=[final_entity], link_preview=False)
        except Exception as e:
            await send_error_log(e, context="Userbot .ping")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
    async def help_cmd(event):
        if event.sender_id != owner_uid:
            return
        await reply_card(uclient, event, HELP_TEXT, collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.speed(?:\s+([\d\.]+))?$"))
    async def speed_cmd(event):
        if event.sender_id != owner_uid:
            return
        if not (event.is_private and event.chat_id == owner_uid):
            return

        arg = event.pattern_match.group(1)
        if not arg:
            curr = user_special_speeds.get(owner_uid, 0.3)
            await send_card(uclient, owner_uid, f"⚡ Current Special Raid Speed Delay: `{curr}s`\nUsage: `.speed 0.5`", collapsed=False)
            return

        try:
            val = float(arg)
            if val < 0.05:
                val = 0.05
            user_special_speeds[owner_uid] = val
            await send_card(uclient, owner_uid, f"✅ Special Raid Speed Delay updated to `{val}s`!", collapsed=False)
        except ValueError:
            await send_card(uclient, owner_uid, "❌ Invalid speed value!", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.timebio\s+(on|off)$"))
    async def timebio_cmd(event):
        if event.sender_id != owner_uid:
            return
        mode = event.pattern_match.group(1).lower()
        if mode == "on":
            if owner_uid in user_timebio_tasks and not user_timebio_tasks[owner_uid].done():
                await reply_card(uclient, event, "⚠️ ᴛɪᴍᴇʙɪᴏ ᴩᴇʜʟᴇ ꜱᴇ ʜɪ ʀᴜɴɴɪɴɢ ʜᴀɪ!", collapsed=False)
                return
            user_timebio_tasks[owner_uid] = asyncio.create_task(timebio_loop())
            await reply_card(uclient, event, "✅ ᴛɪᴍᴇʙɪᴏ ᴇɴᴀʙʟᴇᴅ! ᴩʀᴏꜰɪʟᴇ ʙɪᴏ ʜᴀʀ ᴍɪɴᴜᴛᴇ ɪɴᴅɪᴀɴ ꜱᴛᴀɴᴅᴀʀᴅ ᴛɪᴍᴇ ꜱᴇ ʟɪᴠᴇ ᴜᴩᴅᴀᴛᴇ ʜᴏɢᴀ.", collapsed=False)
        else:
            task = user_timebio_tasks.pop(owner_uid, None)
            if task:
                task.cancel()
            await reply_card(uclient, event, "🛑 ᴛɪᴍᴇʙɪᴏ ᴅɪꜱᴀʙʟᴇᴅ!", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.purge(?:\s+(\d+))?$"))
    async def purge_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            count_arg = event.pattern_match.group(1)
            chat_id = event.chat_id

            try:
                await event.delete()
            except Exception:
                pass

            msg_ids = []
            if reply:
                start_id = reply.id
                async for msg in uclient.iter_messages(chat_id, min_id=start_id - 1):
                    msg_ids.append(msg.id)
                    if len(msg_ids) >= 100:
                        await uclient.delete_messages(chat_id, msg_ids)
                        msg_ids = []
                if msg_ids:
                    await uclient.delete_messages(chat_id, msg_ids)
            elif count_arg:
                count = int(count_arg)
                async for msg in uclient.iter_messages(chat_id, limit=count):
                    msg_ids.append(msg.id)
                    if len(msg_ids) >= 100:
                        await uclient.delete_messages(chat_id, msg_ids)
                        msg_ids = []
                if msg_ids:
                    await uclient.delete_messages(chat_id, msg_ids)
            else:
                inf = await send_card(uclient, chat_id, "⚠️ ᴋɪꜱɪ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.purge` ᴋᴀʀᴇɪɴ ʏᴀ `.purge 50` ꜰᴏʀᴍᴀᴛ ᴜꜱᴇ ᴋᴀʀᴇɪɴ.", collapsed=False)
                await asyncio.sleep(3)
                try:
                    await inf.delete()
                except Exception:
                    pass
                return

            noti = await send_card(uclient, chat_id, "🧹 ᴩᴜʀɢᴇ ᴄᴏᴍᴩʟᴇᴛᴇ! ᴍᴇꜱꜱᴀɢᴇꜱ ᴄʟᴇᴀɴᴇᴅ.", collapsed=False)
            await asyncio.sleep(2)
            try:
                await noti.delete()
            except Exception:
                pass
        except Exception as e:
            await send_error_log(e, context="Userbot .purge")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.tts(?:\s+(.+))?"))
    async def tts_cmd(event):
        if event.sender_id != owner_uid:
            return
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        text = event.pattern_match.group(1)
        
        if not text:
            if reply and (reply.text or reply.message):
                text = reply.text or reply.message
            else:
                await reply_card(uclient, event, "⚠️ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ ᴍᴇ ᴄᴏɴᴠᴇʀᴛ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴛᴇxᴛ ᴅᴇ ʏᴀ ᴍᴇꜱꜱᴀɢᴇ ʀᴇᴩʟʏ ᴋᴀʀᴇɪɴ.", collapsed=False)
                return

        try:
            await event.delete()
        except Exception:
            pass

        file_name = f"tts_{owner_uid}.mp3"
        try:
            tts = gTTS(text=text, lang="hi")
            tts.save(file_name)
            await uclient.send_file(event.chat_id, file_name, voice_note=True, reply_to=reply_to_id)
        except Exception as e:
            await send_card(uclient, event.chat_id, f"❌ TTS Error: `{e}`", collapsed=False)
            await send_error_log(e, context="Userbot .tts")
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    # ========== FIXED AFK SYSTEM ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.afk(?:\s+(.+))?$"))
    async def afk_on(event):
        if event.sender_id != owner_uid:
            return
        reason = event.pattern_match.group(1) or "Busy"
        user_afk_data[owner_uid] = {
            "status": True,
            "reason": reason,
            "start": time.monotonic(),
            "pings": [],
            "replied_users": set(),
            "ignore_ids": set()
        }
        res = await reply_card(uclient, event, f"💤 ᴀꜰᴋ ᴍᴏᴅᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!\nReason: `{reason}`", collapsed=False)
        if res:
            user_afk_data[owner_uid]["ignore_ids"].add(res.id)

    @uclient.on(events.NewMessage(outgoing=True))
    async def afk_off_check(event):
        if event.sender_id != owner_uid:
            return
        if not (owner_uid in user_afk_data and user_afk_data[owner_uid]["status"]):
            return

        text = (event.raw_text or "").strip()
        if text.startswith("."):
            return
        if event.id in user_afk_data[owner_uid]["ignore_ids"]:
            return

        data = user_afk_data.pop(owner_uid)
        dur = int(time.monotonic() - data["start"])
        m, s = divmod(dur, 60)
        h, m = divmod(m, 60)
        seen_time = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
        pings_count = len(data["pings"])

        await reply_card(
            uclient,
            event,
            f"☀️ ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ! ᴀꜰᴋ ᴍᴏᴅᴇ ᴅɪꜱᴀʙʟᴇᴅ.\nᴀᴀᴩ `{seen_time}` ᴛᴀᴋ ᴏꜰꜰʟɪɴᴇ ᴛʜᴇ. ᴍᴇɴᴛɪᴏɴꜱ: `{pings_count}`",
            collapsed=False
        )

    @uclient.on(events.NewMessage(incoming=True))
    async def afk_listener(event):
        if owner_uid not in user_afk_data or not user_afk_data[owner_uid]["status"]:
            return

        should_reply = False
        if event.is_private and event.sender_id != owner_uid:
            should_reply = True
        else:
            if event.mentioned:
                should_reply = True
            elif event.is_reply:
                reply_msg = await event.get_reply_message()
                if reply_msg and reply_msg.sender_id == owner_uid:
                    should_reply = True

        if should_reply:
            data = user_afk_data[owner_uid]
            sender_id = event.sender_id

            if sender_id in data["replied_users"]:
                return

            dur = int(time.monotonic() - data["start"])
            m, s = divmod(dur, 60)
            h, m = divmod(m, 60)
            seen_time = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

            sender = await event.get_sender()
            sname = sender.first_name if sender and sender.first_name else "User"
            data["pings"].append((sender_id, sname))
            data["replied_users"].add(sender_id)

            msg_box = (
                "𝗠ᴀꜱᴛᴇʀ ᴀʙʜɪ ᴀꜰᴋ ʜᴀɪɴ! 💀\n\n"
                f"➥ 𝗥ᴇᴀꜱᴏɴ : {data['reason']}\n\n"
                f"➥ 𝗢ꜰꜰʟɪɴᴇ ꜱɪɴᴄᴇ : {seen_time}"
            )
            entity = MessageEntityBlockquote(offset=0, length=utf16_len(msg_box), collapsed=False)
            try:
                sent = await event.reply(msg_box, formatting_entities=[entity], link_preview=False)
                if sent:
                    data["ignore_ids"].add(sent.id)
            except Exception:
                pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:reboot|stop)$"))
    async def universal_reboot_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            await event.delete()
        except Exception:
            pass

        active_raids[owner_uid].clear()
        active_reply_raids[owner_uid].clear()
        active_special_raids[owner_uid].clear()
        active_special_reply_raids[owner_uid].clear()
        auto_raid_active[owner_uid] = False

        await send_card(
            uclient,
            owner_uid,
            "🛑 [STOP EXECUTED] Saari Raids, Reply Raids aur Spams successfully stop kar di gayi hain!",
            collapsed=False
        )

    # ============================================================
    #            SPECIAL RAID & SPECIAL REPLY RAID ENGINE
    # ============================================================

    @uclient.on(events.NewMessage(outgoing=True))
    async def special_commands_listener(event):
        if event.sender_id != owner_uid:
            return

        raw_text = (event.raw_text or "").strip()
        lower_text = raw_text.lower()
        chat_id = event.chat_id

        if not await is_beta_user(owner_uid):
            return

        try:
            if re.search(r"teri\s+maa\s+di\s+fudi", lower_text):
                reply = await event.get_reply_message()
                if not reply or not reply.sender_id:
                    return

                if await is_protected_user(reply.sender_id):
                    try:
                        await event.delete()
                    except Exception:
                        pass
                    await uclient.send_message(chat_id, PROTECTION_WARNING)
                    await send_card(uclient, owner_uid, f"🛡️ [PROTECTION TRIGGERED] Target `{reply.sender_id}` ek Protected Admin/Owner hai!", collapsed=False)
                    return

                prefix_name = ""
                parts = re.split(r"teri\s+maa\s+di\s+fudi", raw_text, flags=re.IGNORECASE)
                if parts and parts[0].strip():
                    prefix_name = parts[0].strip() + " "

                try:
                    await event.delete()
                except Exception:
                    pass

                target_user_id = reply.sender_id
                active_special_raids[owner_uid][chat_id] = True

                cursor = special_msgs_col.find({}).sort("line_num", 1)
                db_messages = [doc["text"] async for doc in cursor if "text" in doc]
                if not db_messages:
                    db_messages = RAID_TEXTS

                rep_start = (
                    f"⚔️ [SPECIAL RAID ACTIVE]\n"
                    f"Target: `{target_user_id}`\n"
                    f"Prefix: `{prefix_name or 'None'}`\n"
                    f"Chat: `{chat_id}`\n"
                    f"Stop: .reboot in Saved Messages"
                )
                await send_card(uclient, owner_uid, rep_start, collapsed=False)

                idx = 0
                while active_special_raids[owner_uid].get(chat_id, False):
                    base_msg = db_messages[idx % len(db_messages)]
                    idx += 1
                    to_send = f"{prefix_name}{base_msg}".strip()

                    try:
                        target_msg_id = await fetch_target_latest_message(uclient, chat_id, target_user_id, reply.id)
                        await uclient.send_message(chat_id, to_send, reply_to=target_msg_id)
                        speed_delay = user_special_speeds.get(owner_uid, 0.3)
                        await asyncio.sleep(speed_delay)
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 1)
                    except Exception as loop_e:
                        await send_error_log(loop_e, context="Special Raid Loop")
                        break

                active_special_raids[owner_uid].pop(chat_id, None)
                return

            if re.search(r"chamm?ar\s+uth", lower_text):
                reply = await event.get_reply_message()
                if not reply or not reply.sender_id:
                    return

                if await is_protected_user(reply.sender_id):
                    try:
                        await event.delete()
                    except Exception:
                        pass
                    await uclient.send_message(chat_id, PROTECTION_WARNING)
                    await send_card(uclient, owner_uid, f"🛡️ [PROTECTION TRIGGERED] Target `{reply.sender_id}` ek Protected Admin/Owner hai!", collapsed=False)
                    return

                prefix_name = ""
                raw_clean = re.sub(r"(oye\s+)?chamm?ar\s+uth", "", raw_text, flags=re.IGNORECASE).strip()
                if raw_clean:
                    prefix_name = raw_clean + " "

                try:
                    await event.delete()
                except Exception:
                    pass

                active_special_reply_raids[owner_uid][reply.sender_id] = prefix_name
                rrep_txt = (
                    f"⚔️ [SPECIAL REPLY RAID ACTIVE]\n"
                    f"Target: `{reply.sender_id}`\n"
                    f"Prefix: `{prefix_name or 'None'}`\n"
                    f"Stop: .reboot in Saved Messages"
                )
                await send_card(uclient, owner_uid, rrep_txt, collapsed=False)
                return
        except Exception as e:
            await send_error_log(e, context="special_commands_listener")

    @uclient.on(events.NewMessage(incoming=True))
    async def special_reply_raid_worker(event):
        try:
            if event.sender_id in active_special_reply_raids.get(owner_uid, {}):
                if not is_meaningful_message(event):
                    return

                prefix_name = active_special_reply_raids[owner_uid][event.sender_id]
                cursor = special_msgs_col.find({}).sort("line_num", 1)
                db_messages = [doc["text"] async for doc in cursor if "text" in doc]
                if not db_messages:
                    db_messages = RAID_TEXTS

                msg_to_send = f"{prefix_name}{random.choice(db_messages)}".strip()
                try:
                    await event.reply(msg_to_send)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="special_reply_raid_worker")

    # ========== ONE WORD 2.0 WORKFLOW ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.auto$"))
    async def start_auto(event):
        if event.sender_id != owner_uid:
            return
        if not (event.is_private and event.chat_id == owner_uid):
            return

        auto_user_states[owner_uid]["current"] = {"step": "WAITING_LINK"}
        await send_card(uclient, owner_uid, "📍 [ONE WORD 2.0] Target message link bhejo.", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True))
    async def auto_workflow_handler(event):
        if event.sender_id != owner_uid:
            return
        if not (event.is_private and event.chat_id == owner_uid):
            return

        try:
            current_state = auto_user_states.get(owner_uid, {}).get("current")
            if not current_state:
                return

            if current_state.get("step") == "WAITING_LINK":
                link = (event.raw_text or "").strip()
                if link.startswith("."):
                    return
                chat_identifier, msg_id = parse_telegram_link(link)

                if not chat_identifier or not msg_id:
                    await send_card(uclient, owner_uid, "❌ ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ! Direct message link bhejo.", collapsed=False)
                    return

                try:
                    entity = await uclient.get_entity(chat_identifier)
                    target_msg = await uclient.get_messages(entity, ids=msg_id)

                    if not target_msg or isinstance(target_msg, MessageEmpty) or not target_msg.sender_id:
                        auto_user_states[owner_uid].clear()
                        await send_card(uclient, owner_uid, "❌ ᴛᴀʀɢᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ᴍɪꜱꜱɪɴɢ ᴏʀ ᴅᴇʟᴇᴛᴇᴅ!", collapsed=False)
                        return

                    if await is_protected_user(target_msg.sender_id):
                        auto_user_states[owner_uid].clear()
                        await uclient.send_message(entity, PROTECTION_WARNING)
                        await send_card(uclient, owner_uid, f"🛡️ [PROTECTION TRIGGERED] Target `{target_msg.sender_id}` ek Protected Admin/Owner hai!", collapsed=False)
                        return

                    current_state["entity"] = entity
                    current_state["target_user_id"] = target_msg.sender_id
                    current_state["initial_msg_id"] = target_msg.id
                    current_state["step"] = "WAITING_TEXT"

                    await send_card(uclient, owner_uid, "✅ ᴛᴀʀɢᴇᴛ ɪᴅᴇɴᴛɪꜰɪᴇᴅ! Ab wo ᴛᴇxᴛ/ᴡᴏʀᴅꜱ ʙʜᴇᴊᴏ ᴊᴏ ᴀᴛᴛᴀᴄᴋ ᴍᴇ ʙʜᴇᴊɴᴇ ʜᴀɪɴ.", collapsed=False)

                except Exception as e:
                    auto_user_states[owner_uid].clear()
                    await send_card(uclient, owner_uid, f"⚠️ Resolution Error: `{e}`", collapsed=False)

            elif current_state.get("step") == "WAITING_TEXT":
                raw_text = (event.raw_text or "").strip()
                if raw_text.startswith("."):
                    return
                words = raw_text.split()

                current_state["remaining_words"] = words
                current_state["step"] = "RUNNING"
                await run_smart_auto_raid()
        except Exception as e:
            await send_error_log(e, context="auto_workflow_handler")

    # ========== STANDARD RAID & SPAM ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rraid$"))
    async def rraid_cmd(event):
        if event.sender_id != owner_uid:
            return
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.rraid` ʟɪᴋʜᴏ.", collapsed=False)
            return

        if await is_protected_user(reply.sender_id):
            try:
                await event.delete()
            except Exception:
                pass
            await event.respond(PROTECTION_WARNING)
            return

        active_reply_raids[owner_uid].add(reply.sender_id)
        await reply_card(uclient, event, f"⚔️ ʀᴇᴩʟʏ ʀᴀɪᴅ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴏɴ: `{reply.sender_id}`\n\nType `.drraid` or `.reboot` to stop.", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.drraid$"))
    async def drraid_cmd(event):
        if event.sender_id != owner_uid:
            return
        reply = await event.get_reply_message()
        if reply and reply.sender_id in active_reply_raids[owner_uid]:
            active_reply_raids[owner_uid].discard(reply.sender_id)
            await reply_card(uclient, event, f"🛑 ʀᴇᴩʟʏ ʀᴀɪᴅ ꜱᴛᴏᴩᴩᴇᴅ ꜰᴏʀ: `{reply.sender_id}`", collapsed=False)
        else:
            active_reply_raids[owner_uid].clear()
            await reply_card(uclient, event, "🛑 ᴀʟʟ ᴀᴄᴛɪᴠᴇ ʀᴇᴩʟʏ ʀᴀɪᴅꜱ ꜱᴛᴏᴩᴩᴇᴅ!", collapsed=False)

    @uclient.on(events.NewMessage(incoming=True))
    async def reply_raid_listener(event):
        try:
            if event.sender_id in active_reply_raids.get(owner_uid, set()):
                if not is_meaningful_message(event):
                    return
                try:
                    await event.reply(random.choice(RAID_TEXTS))
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="reply_raid_listener")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.raid(?: (.+))?"))
    async def raid_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.raid [count]` ʟᴀɢᴀᴏ.", collapsed=False)
                return

            if await is_protected_user(reply.sender_id):
                try:
                    await event.delete()
                except Exception:
                    pass
                await event.respond(PROTECTION_WARNING)
                return

            try:
                await event.delete()
            except Exception:
                pass

            args = event.pattern_match.group(1)
            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            count = 15
            if args and args.strip().isdigit():
                count = int(args.strip())

            for _ in range(count):
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    target_msg_id = await fetch_target_latest_message(uclient, chat_id, reply.sender_id, reply.id)
                    await uclient.send_message(chat_id, random.choice(RAID_TEXTS), reply_to=target_msg_id)
                    await asyncio.sleep(0.3)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .raid")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.mraid(?: (.+))?"))
    async def mraid_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.mraid [count]` ʟᴀɢᴀᴏ.", collapsed=False)
                return

            if await is_protected_user(reply.sender_id):
                try:
                    await event.delete()
                except Exception:
                    pass
                await event.respond(PROTECTION_WARNING)
                return

            try:
                await event.delete()
            except Exception:
                pass

            args = event.pattern_match.group(1)
            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            count = 15
            if args and args.strip().isdigit():
                count = int(args.strip())

            target_user = reply.sender
            first_name = target_user.first_name if (target_user and target_user.first_name) else "User"
            mention_str = f"[{first_name}](tg://user?id={reply.sender_id}) "

            for _ in range(count):
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    target_msg_id = await fetch_target_latest_message(uclient, chat_id, reply.sender_id, reply.id)
                    await uclient.send_message(chat_id, f"{mention_str}{random.choice(RAID_TEXTS)}", reply_to=target_msg_id)
                    await asyncio.sleep(0.35)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .mraid")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sraid(?: (.+))?"))
    async def sraid_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.sraid` ʟᴀɢᴀᴏ.", collapsed=False)
                return

            if await is_protected_user(reply.sender_id):
                try:
                    await event.delete()
                except Exception:
                    pass
                await event.respond(PROTECTION_WARNING)
                return

            try:
                await event.delete()
            except Exception:
                pass

            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            for _ in range(50):
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    target_msg_id = await fetch_target_latest_message(uclient, chat_id, reply.sender_id, reply.id)
                    await uclient.send_message(chat_id, random.choice(RAID_TEXTS), reply_to=target_msg_id)
                    await asyncio.sleep(0.1)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .sraid")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.oneraid(?: (.+))?"))
    async def oneraid_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.oneraid [count/text]` ʟᴀɢᴀᴏ.", collapsed=False)
                return

            if await is_protected_user(reply.sender_id):
                try:
                    await event.delete()
                except Exception:
                    pass
                await event.respond(PROTECTION_WARNING)
                return

            try:
                await event.delete()
            except Exception:
                pass

            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            args = event.pattern_match.group(1)
            if args and args.strip().isdigit():
                limit = int(args.strip())
                word_sequence = ONE_WORD_RAID_TEXTS[:limit]
            elif args:
                word_sequence = args.strip().split()
            else:
                word_sequence = ONE_WORD_RAID_TEXTS

            for word in word_sequence:
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    target_msg_id = await fetch_target_latest_message(uclient, chat_id, reply.sender_id, reply.id)
                    await uclient.send_message(chat_id, word, reply_to=target_msg_id)
                    await asyncio.sleep(0.2)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .oneraid")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.spam(?: (.+))?"))
    async def spam_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            args = event.pattern_match.group(1)
            if not args:
                await reply_card(uclient, event, "⚠️ Usage: `.spam 10 Text`", collapsed=False)
                return

            try:
                await event.delete()
            except Exception:
                pass

            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            parts = args.strip().split(maxsplit=1)
            if parts[0].isdigit() and len(parts) > 1:
                count = int(parts[0])
                text = parts[1]
            else:
                count = 10
                text = args

            reply = await event.get_reply_message()
            if reply and await is_protected_user(reply.sender_id):
                await event.respond(PROTECTION_WARNING)
                active_raids[owner_uid].discard(chat_id)
                return

            reply_to_id = reply.id if (reply and reply.sender_id) else None

            for _ in range(count):
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    await uclient.send_message(chat_id, text, reply_to=reply_to_id)
                    await asyncio.sleep(0.3)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .spam")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sspam(?: (.+))?"))
    async def special_spam_cmd(event):
        if event.sender_id != owner_uid:
            return
        if not await is_beta_user(owner_uid):
            return

        try:
            args = event.pattern_match.group(1)
            if not args:
                await reply_card(uclient, event, "⚠️ Usage: `.sspam 20 Text`", collapsed=False)
                return

            try:
                await event.delete()
            except Exception:
                pass

            chat_id = event.chat_id
            active_raids[owner_uid].add(chat_id)

            parts = args.strip().split(maxsplit=1)
            if parts[0].isdigit() and len(parts) > 1:
                count = int(parts[0])
                text = parts[1]
            else:
                count = 15
                text = args

            reply = await event.get_reply_message()
            if reply and await is_protected_user(reply.sender_id):
                await event.respond(PROTECTION_WARNING)
                active_raids[owner_uid].discard(chat_id)
                return

            reply_to_id = reply.id if reply else None

            for _ in range(count):
                if chat_id not in active_raids[owner_uid]:
                    break
                try:
                    await uclient.send_message(chat_id, text, reply_to=reply_to_id)
                    await asyncio.sleep(0.15)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_raids[owner_uid].discard(chat_id)
        except Exception as e:
            await send_error_log(e, context="Userbot .sspam")

    # ============================================================
    #       🔥 UNIQUE FUN & ANIMATED SUITE (STEADY & LONG)
    # ============================================================

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.train$"))
    async def train_anim_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            train_frames = [
                "ᴛʀᴀɪɴ ᴀᴩᴩʀᴏᴀᴄʜɪɴɢ ꜱᴛᴀᴛɪᴏɴ...\n\n                                      [o]=o\n═══════════════════════════════════════════",
                "ꜱᴛᴇᴀᴍ ᴇɴɢɪɴᴇ ᴠɪꜱɪʙʟᴇ...\n\n                               .---.  [o]=o\n═══════════════════════════════════════════",
                "ᴄʜᴜᴋ ᴄʜᴜᴋ ᴄʜᴜᴋ ᴄʜᴜᴋ...\n\n                       .---.   |   |  [o]=o\n═══════════════════════════════════════════",
                "ᴇɴᴛᴇʀɪɴɢ ᴩʟᴀᴛꜰᴏʀᴍ...\n\n               .---.   |   |===|   |  [o]=o\n═══════════════════════════════════════════",
                "ꜱᴩᴇᴇᴅ ᴄᴏɴᴛʀᴏʟ ᴢᴏɴᴇ...\n\n       .---.   |   |===|   |===|   |  [o]=o\n═══════════════════════════════════════════",
                "ꜰᴜʟʟ ᴛʀᴀɪɴ ᴏɴ ᴩʟᴀᴛꜰᴏʀᴍ!\n\n.---.  |   |===|   |===|   |===|   |  [o]=o\n═══════════════════════════════════════════",
                "ᴄʀᴏꜱꜱɪɴɢ ᴩʟᴀᴛꜰᴏʀᴍ ᴄᴇɴᴛᴇʀ...\n\n|   |===|   |===|   |===|   |  [o]=o  💨\n═══════════════════════════════════════════",
                "ꜱᴩᴇᴇᴅɪɴɢ ᴜᴩ ᴀᴀɢᴇ ᴋɪ ᴏʀ...\n\n|===|   |===|   |  [o]=o       💨💨💨\n═══════════════════════════════════════════",
                "ʟᴇᴀᴠɪɴɢ ꜱᴛᴀᴛɪᴏɴ ʟɪᴍɪᴛ...\n\n|   |  [o]=o             💨💨💨💨💨\n═══════════════════════════════════════════",
                "ᴀᴀɢᴇ ɴɪᴋᴀʟ ɢᴀʏɪ...\n\n  [o]=o                💨💨💨💨💨💨💨\n═══════════════════════════════════════════",
                "ꜱᴛᴀᴛɪᴏɴ ᴄʟᴇᴀʀᴇᴅ!\n\n💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨\nᴛʀᴀɪɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʀᴏꜱꜱᴇᴅ ᴛʜᴇ ꜱᴛᴀᴛɪᴏɴ!"
            ]

            msg = await send_fun_frame(uclient, event.chat_id, train_frames[0], reply_to=reply_to_id)
            for f in train_frames[1:]:
                await asyncio.sleep(0.45)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .train")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:gadi|car)$"))
    async def car_anim_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            car_frames = [
                "ᴠᴇʜɪᴄʟᴇ ꜱᴩᴏᴛᴛᴇᴅ ᴏɴ ᴛʀᴀᴄᴋ...\n\n                               .---.\n                               '-o-o-'\n═════════════════════════════════════",
                "ᴀᴩᴩʀᴏᴀᴄʜɪɴɢ ᴀᴛ ʜɪɢʜ ꜱᴩᴇᴇᴅ...\n\n                      .---.\n                     '-o-o-'\n═════════════════════════════════════",
                "ꜱᴩᴇᴇᴅ ᴢᴏɴᴇ ᴇɴᴛʀʏ...\n\n            .---.\n           '-o-o-'\n═════════════════════════════════════",
                "ᴄʟᴏꜱᴇ ʀᴀɴɢᴇ ᴛᴜʀʙᴏ...\n\n   .---.\n  '-o-o-'\n═════════════════════════════════════",
                "ꜰᴜʟʟ ᴛʜʀᴏᴛᴛʟᴇ: 180 ᴋᴍ/ʜ!\n\n   .--------.\n  /          \\\n  |  __    __  |\n  \\ (__)  (__) /\n═════════════════════════════════",
                "ꜱᴋʀʀʀʀʀʀᴛ... ᴩᴏᴡᴇʀ ᴅʀɪꜰᴛ!\n\n   .--------.   💨💨💨\n  /   __   __ \\\n  \\  (__) (__) /\n═════════════════════════════════",
                "ꜱᴍᴏᴋᴇ ꜱᴄʀᴇᴇɴ ᴄʀᴇᴀᴛᴇᴅ...\n\n💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨💨\n⚡ ꜱʏꜱᴛᴇᴍ ᴏɴ ᴛᴏᴩ • ʀᴀꜱᴛᴀ ꜱᴀᴀꜰ ᴋᴀʀᴏ! ⚡"
            ]

            msg = await send_fun_frame(uclient, event.chat_id, car_frames[0], reply_to=reply_to_id)
            for f in car_frames[1:]:
                await asyncio.sleep(0.45)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .car")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:rocket|launch)$"))
    async def rocket_anim_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            rocket_frames = [
                "ʟᴀᴜɴᴄʜ ᴩᴀᴅ ꜱᴇᴛᴜᴩ ʀᴇᴀᴅʏ...\n\n      /\\\n     |  |\n    /|  |\\\n    ==  ==\n═══════════\nᴛ-ᴍɪɴᴜꜱ 4ꜱ...",
                "ꜱʏꜱᴛᴇᴍ ᴄʜᴇᴄᴋ ᴄᴏᴍᴩʟᴇᴛᴇ...\n\n      /\\\n     |  |\n    /|  |\\\n    ==  ==\n═══════════\nᴛ-ᴍɪɴᴜꜱ 3ꜱ...",
                "ᴛʜʀᴜꜱᴛᴇʀꜱ ᴩʀᴇ-ʜᴇᴀᴛɪɴɢ...\n\n      /\\\n     |  |\n    /|  |\\\n     (🔥)\n═══════════\nᴛ-ᴍɪɴᴜꜱ 2ꜱ...",
                "ɪɢɴɪᴛɪᴏɴ ꜱᴛᴀʀᴛᴇᴅ...\n\n      /\\\n     |  |\n    /|  |\\\n    (💥💥)\n═══════════\nᴛ-ᴍɪɴᴜꜱ 1ꜱ...",
                "ʙʟᴀꜱᴛ ᴏꜰꜰ!!\n\n      /\\\n     |  |\n    /|  |\\\n   (🔥🔥🔥)\n  💨💨💨💨💨",
                "ʟᴇᴀᴠɪɴɢ ᴀᴛᴍᴏꜱᴩʜᴇʀᴇ...\n\n      /\\\n     |  |\n\n  💨💨💨💨💨💨\n  💨💨💨💨💨💨",
                "🚀 ᴍɪꜱꜱɪᴏɴ ᴀᴄᴄᴏᴍᴩʟɪꜱʜᴇᴅ!\n\n🌌 🪐 🛰️ ✨\nᴛᴀʀɢᴇᴛ ᴋᴏ ꜱᴩᴀᴄᴇ ᴏʀʙɪᴛ ᴍᴇ ᴩʜᴇɴᴋ ᴅɪʏᴀ ɢᴀʏᴀ!"
            ]

            msg = await send_fun_frame(uclient, event.chat_id, rocket_frames[0], reply_to=reply_to_id)
            for f in rocket_frames[1:]:
                await asyncio.sleep(0.45)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .rocket")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:scan|hack)$"))
    async def scan_hack_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            target_name = "ᴛᴀʀɢᴇᴛ ɴᴏᴅᴇ"
            if reply and reply.sender:
                target_name = reply.sender.first_name or "ᴛᴀʀɢᴇᴛ"

            scan_frames = [
                f"🖥️ [ɪɴɪᴛɪᴀʟɪᴢɪɴɢ] {target_name}\n[░░░░░░░░░░] 0%",
                "📡 [ꜱᴄᴀɴɴɪɴɢ ᴏᴩᴇɴ ᴩᴏʀᴛꜱ]...\n[██░░░░░░░░] 15%",
                "🛡️ [ʙʏᴩᴀꜱꜱɪɴɢ ꜰɪʀᴇᴡᴀʟʟ ʟᴀʏᴇʀ 1]...\n[███░░░░░░░] 30%",
                "🛡️ [ʙʏᴩᴀꜱꜱɪɴɢ ꜰɪʀᴇᴡᴀʟʟ ʟᴀʏᴇʀ 2]...\n[█████░░░░░] 50%",
                "🔓 [ɪɴᴊᴇᴄᴛɪɴɢ ꜱʏꜱᴛᴇᴍ ᴇxᴩʟᴏɪᴛ]...\n[███████░░░] 70%",
                "💾 [ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴅᴀᴛᴀʙᴀꜱᴇ ᴩᴀᴄᴋᴇᴛꜱ]...\n[█████████░] 90%",
                "⚡ [ᴄʟᴇᴀʀɪɴɢ ꜱʏꜱᴛᴇᴍ ʟᴏɢꜱ]...\n[██████████] 100%",
                (
                    f"⚠️ [ꜱʏꜱᴛᴇᴍ ᴄᴏᴍᴩʀᴏᴍɪꜱᴇᴅ] ⚠️\n\n"
                    f"👤 ᴛᴀʀɢᴇᴛ: {target_name}\n"
                    f"🌐 ɪᴩ: 192.168.0.{random.randint(10, 250)}\n"
                    "⚡ ꜱᴛᴀᴛᴜꜱ: ʀᴏᴏᴛ ᴀᴄᴄᴇꜱꜱ ɢʀᴀɴᴛᴇᴅ!\n"
                    "💀 ꜱʏꜱᴛᴇᴍ ᴏᴠᴇʀʀɪᴅᴇ ᴄᴏᴍᴩʟᴇᴛᴇ"
                )
            ]

            msg = await send_fun_frame(uclient, event.chat_id, scan_frames[0], reply_to=reply_to_id)
            for f in scan_frames[1:]:
                await asyncio.sleep(0.45)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .scan")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.matrix$"))
    async def matrix_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            matrix_frames = [
                (
                    "🟢 ⚡ [ɪɴɪᴛɪᴀʟɪᴢɪɴɢ ɴᴇᴜʀᴀʟ ᴍᴀᴛʀɪx ꜱᴛʀᴇᴀᴍ] ⚡ 🟢\n\n"
                    "0 1 0 0 1 0 0 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 0 1 0 1 0 1\n"
                    "1 0 1 1 0 0 0 1 1 0 1 0 0 1 1 0 1 1 0 1 0 0 1 0 1 0 1 1\n"
                    "0 0 1 0 1 1 0 1 0 1 1 1 0 0 1 1 0 0 1 1 0 1 0 1 0 0 1 0\n"
                    "1 1 0 1 0 0 1 0 0 0 1 0 1 1 0 1 1 0 0 1 0 1 1 0 1 1 0 1\n"
                    "0 1 1 0 1 1 0 1 1 0 1 1 0 0 0 1 0 1 0 0 1 1 1 0 0 1 0 1\n"
                    "1 0 0 1 0 1 0 1 0 1 0 0 1 0 1 1 1 1 0 1 0 0 1 0 1 1 1 0\n"
                    "0 1 0 0 1 1 1 0 1 1 0 1 0 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0\n"
                    "1 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 1 0 1 1 0 0 1 0 1 0 0 1\n"
                    "0 0 1 1 0 1 0 1 0 1 0 0 1 1 1 0 0 1 0 1 1 0 1 0 1 1 0 0\n"
                    "1 1 0 0 0 1 1 0 0 0 1 0 1 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1\n"
                    "░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\n"
                    "[ ꜱᴛᴀᴛᴜꜱ: ᴄᴏɴɴᴇᴄᴛɪɴɢ ᴛᴏ ɢʟᴏʙᴀʟ ᴍᴀɪɴꜰʀᴀᴍᴇ | 15% ]"
                ),
                (
                    "🟢 ⚡ [ᴅɪɢɪᴛᴀʟ ᴄᴏᴅᴇ ʀᴀɪɴ: ʟᴇᴠᴇʟ 1] ⚡ 🟢\n\n"
                    "ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ ｵ ﾘ ｱ ﾎ ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ\n"
                    "1 0 1 0 1 1 0 1 0 0 1 0 1 1 0 1 1 0 1 1 0 0 1 0 1 0 0 1\n"
                    "0 1 0 0 1 1 1 0 1 1 0 1 0 0 1 0 0 1 1 0 1 0 1 1 0 0 1 0\n"
                    "ｽ ﾀ ﾇ ﾍ ｦ ｲ ｸ ｺ ｿ ﾁ ﾄ ﾉ ﾌ ﾔ ﾖ ﾙ ﾚ ﾛ ﾝ 0 1 0 1 0 0 1 1 0\n"
                    "1 0 0 1 0 1 0 1 0 1 0 0 1 0 1 1 1 1 0 1 0 0 1 0 1 1 1 0\n"
                    "0 0 1 0 1 1 0 1 1 0 1 1 0 0 0 1 0 1 0 0 1 1 1 0 0 1 0 1\n"
                    "0x4F 0xA1 0x7E 0x9C 0xB4 0x2D 0x8F 0x1A 0xC3 0x55 0xE9 0xF0\n"
                    "1 1 0 0 0 1 1 0 0 0 1 0 1 1 1 0 1 0 1 0 0 1 1 0 0 1 0 1\n"
                    "0 1 1 1 0 0 1 0 1 1 0 1 0 1 0 1 0 0 1 1 0 1 0 1 0 0 1 0\n"
                    "ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ ｵ ﾘ ｱ ﾎ\n"
                    "▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\n"
                    "[ ꜱᴛᴀᴛᴜꜱ: ʙʏᴩᴀꜱꜱɪɴɢ ꜱᴇᴄᴜʀɪᴛʏ ꜰɪʀᴇᴡᴀʟʟꜱ | 35% ]"
                ),
                (
                    "🟢 ⚡ [ᴅᴇᴇᴩ ᴄʏʙᴇʀ ꜱᴛʀᴇᴀᴍ: ʟᴇᴠᴇʟ 2] ⚡ 🟢\n\n"
                    "0xAA 0xBB 0xCC 0xDD 0xEE 0xFF 0x00 0x11 0x22 0x33 0x44 0x55\n"
                    "ﾎ ﾘ ｱ ｵ ﾂ ﾜ ｻ ﾆ ﾓ ﾅ ｼ ｳ ｰ ﾋ ﾐ ﾊ ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ\n"
                    "1 0 1 1 0 0 1 0 1 0 0 1 1 1 0 0 1 0 1 0 1 1 0 1 0 0 1 0\n"
                    "0 1 1 0 1 0 1 1 0 0 1 0 1 1 0 1 0 1 0 0 1 1 1 0 1 1 0 1\n"
                    "ﾍ ﾇ ﾀ ｽ ﾈ ｾ ﾗ ﾕ ﾑ ｷ ｶ ｴ ﾒ ｹ ﾏ ﾃ ｦ ｲ ｸ ｺ ｿ ﾁ ﾄ ﾉ ﾌ ﾔ ﾖ ﾙ\n"
                    "0x12 0x34 0x56 0x78 0x9A 0xBC 0xDE 0xF0 0xAA 0x55 0xFF 0x00\n"
                    "1 1 0 1 0 0 1 0 1 1 1 0 0 1 0 1 1 0 0 1 0 1 0 1 0 1 0 0\n"
                    "0 0 1 0 1 1 0 1 1 0 1 1 0 0 0 1 0 1 0 0 1 1 1 0 0 1 0 1\n"
                    "ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ ｵ ﾘ ｱ ﾎ ｽ ﾀ ﾇ ﾍ ｦ ｲ ｸ ｺ ｿ ﾁ ﾄ ﾉ\n"
                    "0xDE 0xAD 0xBE 0xEF 0xCA 0xFE 0xBA 0xBE 0x00 0x01 0x02 0x03\n"
                    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\n"
                    "[ ꜱᴛᴀᴛᴜꜱ: ɪɴᴊᴇᴄᴛɪɴɢ ɴᴇᴜʀᴀʟ ᴩᴀᴄᴋᴇᴛꜱ | 58% ]"
                ),
                (
                    "🟢 ⚡ [ᴄᴏᴅᴇ ᴏᴠᴇʀʟᴏᴀᴅ: ʟᴇᴠᴇʟ 3] ⚡ 🟢\n\n"
                    "0 1 0 0 1 1 1 0 0 1 0 1 0 1 0 0 1 0 1 1 0 0 1 0 1 0 0 1\n"
                    "ﾎ ﾘ ｱ ｵ ﾂ ﾜ ｻ ﾆ ﾓ ﾅ ｼ ｳ ｰ ﾋ ﾐ ﾊ ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ\n"
                    "0xAA 0xBB 0xCC 0xDD 0xEE 0xFF 0x00 0x99 0x88 0x77 0x66 0x55\n"
                    "1 1 0 1 0 0 1 0 1 1 1 0 0 1 0 1 0 1 0 0 1 1 1 0 1 1 0 1\n"
                    "ﾍ ﾇ ﾀ ｽ ﾈ ｾ ﾗ ﾕ ﾑ ｷ ｶ ｴ ﾒ ｹ ﾏ ﾃ ｦ ｲ ｸ ｺ ｿ ﾁ ﾄ ﾉ ﾌ ﾔ ﾖ ﾙ\n"
                    "0 0 1 0 1 1 0 1 1 0 1 1 0 0 0 1 1 0 1 0 1 1 0 1 0 0 1 0\n"
                    "0xFE 0xDC 0xBA 0x98 0x76 0x54 0x32 0x10 0x11 0x33 0x55 0x77\n"
                    "1 0 1 1 0 0 1 0 1 0 0 1 1 1 0 0 0 1 1 0 1 0 1 1 0 0 1 0\n"
                    "ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ ｽ ﾀ ﾇ ﾍ ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ\n"
                    "0x01 0x02 0x04 0x08 0x10 0x20 0x40 0x80 0x00 0xFF 0xAA 0x55\n"
                    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░░\n"
                    "[ ꜱᴛᴀᴛᴜꜱ: ꜱʏꜱᴛᴇᴍ ᴄᴏʀᴇ ᴏᴠᴇʀʀɪᴅᴇ | 79% ]"
                ),
                (
                    "🟢 ⚡ [ɴᴇᴜʀᴀʟ ɴᴇᴛᴡᴏʀᴋ ʙʀᴇᴀᴄʜ] ⚡ 🟢\n\n"
                    "1 1 0 0 1 0 1 0 0 1 0 1 1 1 0 0 1 0 1 1 0 0 1 0 1 0 0 1\n"
                    "0xDE 0xAD 0xC0 0xDE 0xBA 0xD0 0x00 0x01 0x02 0x03 0x04 0x05\n"
                    "ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ ｵ ﾘ ｱ ﾎ ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ\n"
                    "0 1 1 0 1 0 0 1 1 1 0 1 0 0 1 0 0 1 0 0 1 1 1 0 1 1 0 1\n"
                    "0x00 0xFF 0x7F 0x80 0x3F 0xC0 0x1F 0xE0 0x0F 0xF0 0x07 0xF8\n"
                    "ｽ ﾀ ﾇ ﾍ ｦ ｲ ｸ ｺ ｿ ﾁ ﾄ ﾉ ﾌ ﾔ ﾖ ﾙ ﾚ ﾛ ﾝ 0 1 0 1 0 0 1 1 0\n"
                    "1 0 1 0 0 1 1 1 0 0 1 0 1 1 0 1 1 1 0 1 0 0 1 0 1 1 1 0\n"
                    "0xAA 0x55 0xCC 0x33 0xF0 0x0F 0xFF 0x00 0x12 0x34 0x56 0x78\n"
                    "ﾃ ﾏ ｹ ﾒ ｴ ｶ ｷ ﾑ ﾕ ﾗ ｾ ﾈ ﾊ ﾐ ﾋ ｰ ｳ ｼ ﾅ ﾓ ﾆ ｻ ﾜ ﾂ ｵ ﾘ ｱ ﾎ\n"
                    "1 1 1 0 0 0 1 1 0 1 0 1 0 0 1 1 0 1 1 0 1 0 1 1 0 0 1 0\n"
                    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░░░░░░░░░░░░░░░░░░\n"
                    "[ ꜱᴛᴀᴛᴜꜱ: ꜱʏɴᴄʜʀᴏɴɪᴢɪɴɢ ɢʟᴏʙᴀʟ ɴᴏᴅᴇꜱ | 94% ]"
                ),
                (
                    "🟢 ⚡ [ᴍᴀᴛʀɪx ꜰᴜʟʟ ꜱʏɴᴄ] ⚡ 🟢\n\n"
                    "01000001 01010101 01010100 01001111 01001101 01000001\n"
                    "01010100 01001001 01001100 00100000 01000011\n"
                    "01001111 01010010 01000101 00100000 01000001 01000011\n"
                    "01010100 01001001 01010110 01000001 01001000 01000100\n"
                    "01000100 00100000 01010011 01011001 01010011 01010100\n"
                    "01000101 01001101 00100000 01001111 01010110 01000101\n"
                    "01010010 01010010 01001001 01000100 01000101 00100000\n"
                    "01000011 01001111 01001101 01010000 01001100 01000101\n"
                    "01010100 01000101 01000100 00100001 00100001 00100001\n"
                    "▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓▓\n"
                    "[ ᴍᴀɪɴꜰʀᴀᴍᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʙʀᴇᴀᴄʜᴇᴅ & ᴏᴠᴇʀʀɪᴅᴅᴇɴ ]\n\n"
                    "⚡ ᴡᴇʟᴄᴏᴍᴇ ᴛᴏ ᴛʜᴇ ʀᴇᴀʟ ᴡᴏʀʟᴅ • ꜱʏꜱᴛᴇᴍ ꜰᴜʟʟʏ ᴄᴏɴɴᴇᴄᴛᴇᴅ ⚡"
                )
            ]

            msg = await send_fun_frame(uclient, event.chat_id, matrix_frames[0], reply_to=reply_to_id)
            for f in matrix_frames[1:]:
                await asyncio.sleep(0.48)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .matrix")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bomb$"))
    async def bomb_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            bomb_frames = [
                "💣 [ᴛɪᴍᴇ ʙᴏᴍʙ ᴩʟᴀɴᴛᴇᴅ]\n⏱️ ᴛ-5ꜱ...",
                "💣 [ᴛɪᴄᴋɪɴɢ ꜰᴀꜱᴛ]\n⏱️ ᴛ-4ꜱ...",
                "🧨 [ꜰᴜꜱᴇ ʙᴜʀɴɪɴɢ]\n⏱️ ᴛ-3ꜱ...",
                "🚨 [ᴅᴀɴɢᴇʀ ᴢᴏɴᴇ]\n⏱️ ᴛ-2ꜱ...",
                "⚠️ [ɪᴍᴩᴀᴄᴛ ɪᴍᴍɪɴᴇɴᴛ]\n⏱️ ᴛ-1ꜱ...",
                "💥💥💥 ʙᴏᴏᴏᴏᴏᴏᴍᴍᴍ! 💥💥💥\n\n💨 ᴛᴀʀɢᴇᴛ ᴅʜᴜᴇɴ ᴍᴇ ɢᴀʏᴀʙ!"
            ]

            msg = await send_fun_frame(uclient, event.chat_id, bomb_frames[0], reply_to=reply_to_id)
            for f in bomb_frames[1:]:
                await asyncio.sleep(0.45)
                try:
                    await edit_fun_frame(msg, f)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .bomb")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.loading(?: (.+))?"))
    async def loading_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None
            text = event.pattern_match.group(1) or "Process Complete"

            try:
                await event.delete()
            except Exception:
                pass

            bars = [
                "⚙️ `Processing:` [▱▱▱▱▱▱▱▱▱▱] 0%",
                "⚙️ `Processing:` [▰▰▰▱▱▱▱▱▱▱] 30%",
                "⚙️ `Processing:` [▰▰▰▰▰▰▱▱▱▱] 60%",
                "⚙️ `Processing:` [▰▰▰▰▰▰▰▰▰▱] 90%",
                f"✅ `Success:` [▰▰▰▰▰▰▰▰▰▰] 100%\n\n✨ **{text}**"
            ]

            msg = await send_fun_frame(uclient, event.chat_id, bars[0], reply_to=reply_to_id)
            for b in bars[1:]:
                await asyncio.sleep(0.35)
                try:
                    await edit_fun_frame(msg, b)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .loading")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.heart$"))
    async def heart_anim_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            hearts = ["❤️", "🧡", "💛", "💚", "💙", "💜", "💖 ✨ LOVE OVERLOADED ✨ 💖"]
            msg = await send_fun_frame(uclient, event.chat_id, hearts[0], reply_to=reply_to_id)
            for h in hearts[1:]:
                await asyncio.sleep(0.30)
                try:
                    await edit_fun_frame(msg, h)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .heart")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.glitch(?: (.+))?"))
    async def glitch_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None
            text = event.pattern_match.group(1)

            if not text:
                if reply and (reply.text or reply.message):
                    text = reply.text or reply.message
                else:
                    await reply_card(uclient, event, "⚠️ Usage: `.glitch text` ya kisi msg pe reply karo.", collapsed=False)
                    return

            try:
                await event.delete()
            except Exception:
                pass

            glitched = make_glitch_text(text)
            await uclient.send_message(event.chat_id, glitched, reply_to=reply_to_id, link_preview=False)
        except Exception as e:
            await send_error_log(e, context="Userbot .glitch")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.flip(?: (.+))?"))
    async def flip_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None
            text = event.pattern_match.group(1)

            if not text:
                if reply and (reply.text or reply.message):
                    text = reply.text or reply.message
                else:
                    await reply_card(uclient, event, "⚠️ Usage: `.flip your text` ya msg pe reply karo.", collapsed=False)
                    return

            try:
                await event.delete()
            except Exception:
                pass

            flipped = make_flipped_text(text)
            await uclient.send_message(event.chat_id, flipped, reply_to=reply_to_id, link_preview=False)
        except Exception as e:
            await send_error_log(e, context="Userbot .flip")

    # ========== OTHER STANDARD UTILITIES ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:type|typ)(?: (.+))?"))
    async def type_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None
            text = event.pattern_match.group(1)
            
            if not text:
                if reply and (reply.text or reply.message):
                    text = reply.text or reply.message
                else:
                    await reply_card(uclient, event, "⚠️ Usage: `.type Aapka Text Yahan`", collapsed=False)
                    return

            try:
                await event.delete()
            except Exception:
                pass

            styled_text = fontify(text)
            typing_symbol = "▒"
            accumulated = ""

            msg = await uclient.send_message(event.chat_id, typing_symbol, reply_to=reply_to_id, link_preview=False)
            for char in styled_text:
                accumulated += char
                try:
                    await msg.edit(f"{accumulated}{typing_symbol}", link_preview=False)
                    await asyncio.sleep(0.20)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    pass

            try:
                await msg.edit(accumulated, link_preview=False)
            except Exception:
                pass
        except Exception as e:
            await send_error_log(e, context="Userbot .type")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fuck$"))
    async def fuck_anim_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            reply_to_id = reply.id if reply else None

            try:
                await event.delete()
            except Exception:
                pass

            frames = [
                "....................../´¯/)\n"
                "....................,/¯../",

                "....................../´¯/)\n"
                "....................,/¯../\n"
                ".................../..../\n"
                "............./´¯/'...'/´¯¯`·¸",

                "....................../´¯/)\n"
                "....................,/¯../\n"
                ".................../..../\n"
                "............./´¯/'...'/´¯¯`·¸\n"
                "........../'/.../..../......./¨¯\\",

                "....................../´¯/)\n"
                "....................,/¯../\n"
                ".................../..../\n"
                "............./´¯/'...'/´¯¯`·¸\n"
                "........../'/.../..../......./¨¯\\\n"
                "........('(...´...´.... ¯~/'...')\n"
                ".........\\.................'...../",

                "....................../´¯/)\n"
                "....................,/¯../\n"
                ".................../..../\n"
                "............./´¯/'...'/´¯¯`·¸\n"
                "........../'/.../..../......./¨¯\\\n"
                "........('(...´...´.... ¯~/'...')\n"
                ".........\\.................'...../\n"
                "..........''...\\.......... _.·´\n"
                "............\\..............(\n"
                "..............\\.............\\..."
            ]

            msg = await uclient.send_message(event.chat_id, frames[0], reply_to=reply_to_id, link_preview=False)
            for f in frames[1:]:
                await asyncio.sleep(0.35)
                try:
                    await msg.edit(f, link_preview=False)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .fuck")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.clone$"))
    async def clone_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                await reply_card(uclient, event, "⚠️ ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.clone` ʀᴜɴ ᴋᴀʀᴏ.", collapsed=False)
                return

            try:
                await event.delete()
            except Exception:
                pass

            if await is_protected_user(reply.sender_id):
                await event.respond(PROTECTION_WARNING)
                return

            msg = await send_card(uclient, event.chat_id, "🔄 ᴄʟᴏɴɪɴɢ ᴛᴀʀɢᴇᴛ ᴩʀᴏꜰɪʟᴇ ɪᴅᴇɴᴛɪᴛʏ...", collapsed=False)
            try:
                target_user = await uclient.get_entity(reply.sender_id)
            except Exception as e:
                await edit_card(msg, f"❌ Failed to fetch user: `{e}`", collapsed=False)
                return

            try:
                me = await uclient.get_me()
                full_me = await uclient(GetFullUserRequest(me.id))
                
                if owner_uid not in backup_profiles:
                    backup_profiles[owner_uid] = {
                        "first_name": me.first_name or "",
                        "last_name": me.last_name or "",
                        "about": full_me.full_user.about or "",
                    }

                full_target = await uclient(GetFullUserRequest(target_user.id))
                target_first = target_user.first_name or "Clone"
                target_last = target_user.last_name or ""
                target_bio = full_target.full_user.about or ""

                if len(target_bio) > 70:
                    target_bio = target_bio[:67] + "..."

                await uclient(UpdateProfileRequest(
                    first_name=target_first,
                    last_name=target_last,
                    about=target_bio
                ))

                if target_user.photo:
                    photo_file = f"clone_{owner_uid}.jpg"
                    downloaded = await uclient.download_profile_photo(target_user, file=photo_file)
                    if downloaded:
                        uploaded = await uclient.upload_file(photo_file)
                        await uclient(UploadProfilePhotoRequest(file=uploaded))
                        if os.path.exists(photo_file):
                            os.remove(photo_file)

                await edit_card(msg, f"✅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʟᴏɴᴇᴅ {target_first}!\n\nType `.back` to restore original profile.", collapsed=False)
            except AboutTooLongError:
                await edit_card(msg, "⚠️ ᴛᴀʀɢᴇᴛ ʙɪᴏ ɪꜱ ᴛᴏᴏ ʟᴏɴɢ, ᴄʟᴏɴᴇᴅ ɴᴀᴍᴇ ᴏɴʟʏ.", collapsed=False)
            except Exception as e:
                await edit_card(msg, f"❌ Clone Error: `{e}`", collapsed=False)
                await send_error_log(e, context="Userbot .clone (execution)")
        except Exception as e:
            await send_error_log(e, context="Userbot .clone")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.back$"))
    async def back_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            try:
                await event.delete()
            except Exception:
                pass

            if owner_uid not in backup_profiles:
                await send_card(uclient, event.chat_id, "⚠️ ᴋᴏɪ ᴩʀᴏꜰɪʟᴇ ʙᴀᴄᴋᴜᴩ ɴᴀʜɪ ᴍɪʟᴀ ʏᴀ ᴀᴀᴩ ᴩᴇʜʟᴇ ꜱᴇ ᴏʀɪɢɪɴᴀʟ ꜱᴛᴀᴛᴇ ᴍᴇ ʜᴀɪɴ.", collapsed=False)
                return

            msg = await send_card(uclient, event.chat_id, "🔄 ʀᴇꜱᴛᴏʀɪɴɢ ᴏʀɪɢɪɴᴀʟ ᴩʀᴏꜰɪʟᴇ...", collapsed=False)
            data = backup_profiles[owner_uid]

            try:
                await uclient(UpdateProfileRequest(
                    first_name=data["first_name"],
                    last_name=data["last_name"],
                    about=data["about"]
                ))

                photos = await uclient.get_profile_photos("me")
                if photos:
                    await uclient(DeletePhotosRequest([photos[0]]))

                del backup_profiles[owner_uid]
                await edit_card(msg, "✅ ᴩʀᴏꜰɪʟᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴛᴏʀᴇᴅ ᴛᴏ ᴏʀɪɢɪɴᴀʟ ɪᴅᴇɴᴛɪᴛʏ!", collapsed=False)
            except Exception as e:
                await edit_card(msg, f"❌ Restore Error: `{e}`", collapsed=False)
                await send_error_log(e, context="Userbot .back (execution)")
        except Exception as e:
            await send_error_log(e, context="Userbot .back")

    # ========== CHUP & BOL SILENT SUITE ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chup(?:\s+(all))?$"))
    async def chup_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            arg = event.pattern_match.group(1)
            chat_id = event.chat_id

            if arg and arg.lower() == "all":
                try:
                    await event.delete()
                except Exception:
                    pass
                u_chup_all[owner_uid].add(chat_id)
                try:
                    await send_card(uclient, owner_uid, f"🔇 ꜱɪʟᴇɴᴛ ᴍᴜᴛᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!\nChat ID: `{chat_id}`\nMode: ALL incoming messages auto-delete.", collapsed=False)
                except Exception:
                    pass
                return

            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
                try:
                    await event.delete()
                except Exception:
                    pass
                try:
                    await send_card(uclient, owner_uid, "⚠️ ᴄʜᴜᴩ ᴄᴏᴍᴍᴀɴᴅ ꜰᴀɪʟᴇᴅ: ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴀʀ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.chup` ʟᴀɢᴀᴏ ʏᴀ `.chup all` ᴜꜱᴇ ᴋᴀʀᴏ.", collapsed=False)
                except Exception:
                    pass
                return

            target_id = reply.sender_id
            if await is_protected_user(target_id):
                try:
                    await event.delete()
                except Exception:
                    pass
                await event.respond(PROTECTION_WARNING)
                return

            try:
                await event.delete()
            except Exception:
                pass

            if chat_id not in u_chup_targets[owner_uid]:
                u_chup_targets[owner_uid][chat_id] = set()
            u_chup_targets[owner_uid][chat_id].add(target_id)

            try:
                await send_card(uclient, owner_uid, f"🤐 ᴛᴀʀɢᴇᴛ ꜱɪʟᴇɴᴄᴇᴅ ꜱɪʟᴇɴᴛʟʏ!\nTarget ID: `{target_id}`\nChat ID: `{chat_id}`", collapsed=False)
            except Exception:
                pass
        except Exception as e:
            await send_error_log(e, context="Userbot .chup")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bol(?:\s+(all))?$"))
    async def bol_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            try:
                await event.delete()
            except Exception:
                pass

            arg = event.pattern_match.group(1)
            chat_id = event.chat_id
            is_master = (owner_uid == OWNER_ID)

            if arg and arg.lower() == "all":
                if is_master:
                    for uid in u_chup_all:
                        u_chup_all[uid].discard(chat_id)
                else:
                    u_chup_all[owner_uid].discard(chat_id)

                try:
                    await send_card(uclient, owner_uid, f"🔊 ɢʀᴏᴜᴩ ᴜɴᴍᴜᴛᴇᴅ!\nChat ID: `{chat_id}`\nMode: Sabhi normal baat kar sakte hain.", collapsed=False)
                except Exception:
                    pass
                return

            reply = await event.get_reply_message()
            if reply and reply.sender_id:
                target_id = reply.sender_id
                if is_master:
                    for uid in u_chup_targets:
                        if chat_id in u_chup_targets[uid]:
                            u_chup_targets[uid][chat_id].discard(target_id)
                else:
                    if chat_id in u_chup_targets[owner_uid]:
                        u_chup_targets[owner_uid][chat_id].discard(target_id)

                try:
                    await send_card(uclient, owner_uid, f"🗣️ ᴛᴀʀɢᴇᴛ ᴜɴ-ꜱɪʟᴇɴᴄᴇᴅ!\nTarget ID: `{target_id}`\nChat ID: `{chat_id}`", collapsed=False)
                except Exception:
                    pass
            else:
                if is_master:
                    for uid in u_chup_targets:
                        if chat_id in u_chup_targets[uid]:
                            u_chup_targets[uid][chat_id].clear()
                    for uid in u_chup_all:
                        u_chup_all[uid].discard(chat_id)
                else:
                    if chat_id in u_chup_targets[owner_uid]:
                        u_chup_targets[owner_uid][chat_id].clear()
                    u_chup_all[owner_uid].discard(chat_id)

                try:
                    await send_card(uclient, owner_uid, f"🔊 ᴄʜᴀᴛ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴꜱ ᴄʟᴇᴀʀᴇᴅ!\nChat ID: `{chat_id}`", collapsed=False)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .bol")

    @uclient.on(events.NewMessage(incoming=True))
    async def incoming_cleaner_and_silencer(event):
        try:
            chat_id = event.chat_id

            if chat_id in u_cleaning_chats.get(owner_uid, set()):
                try:
                    await event.delete()
                except Exception:
                    pass
                return

            if chat_id in u_chup_all.get(owner_uid, set()):
                if not await is_protected_user(event.sender_id) and event.sender_id != owner_uid:
                    try:
                        await event.delete()
                    except Exception:
                        pass
                return

            targets = u_chup_targets.get(owner_uid, {}).get(chat_id, set())
            if event.sender_id in targets:
                if not await is_protected_user(event.sender_id):
                    try:
                        await event.delete()
                    except Exception:
                        pass
        except Exception:
            pass

    async def run_cleaner_task(chat_id: int):
        try:
            async for msg in uclient.iter_messages(chat_id, limit=500):
                if chat_id not in u_cleaning_chats.get(owner_uid, set()):
                    break
                try:
                    await msg.delete()
                    await asyncio.sleep(0.08)
                except Exception:
                    continue
        except Exception as e:
            await send_error_log(e, context="run_cleaner_task")

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.cleaning\s+(on|off)$"))
    async def cleaning_cmd(event):
        if event.sender_id != owner_uid:
            return
        try:
            try:
                await event.delete()
            except Exception:
                pass

            mode = event.pattern_match.group(1).lower()
            chat_id = event.chat_id

            if mode == "on":
                u_cleaning_chats[owner_uid].add(chat_id)
                asyncio.create_task(run_cleaner_task(chat_id))
                try:
                    await send_card(uclient, owner_uid, f"🧹 ᴄʟᴇᴀɴɪɴɢ ꜱᴛᴀʀᴛᴇᴅ ꜱɪʟᴇɴᴛʟʏ!\nChat ID: `{chat_id}`\nMode: Deleting all chat messages.", collapsed=False)
                except Exception:
                    pass
            else:
                u_cleaning_chats[owner_uid].discard(chat_id)
                try:
                    await send_card(uclient, owner_uid, f"🛑 ᴄʟᴇᴀɴɪɴɢ ꜱᴛᴏᴩᴩᴇᴅ!\nChat ID: `{chat_id}`", collapsed=False)
                except Exception:
                    pass
        except Exception as e:
            await send_error_log(e, context="Userbot .cleaning")

# ============================================================
#         RENDER / RAILWAY HTTP WEB SERVER
# ============================================================

async def handle_ping(request):
    return web.Response(text="ASHISH X HOSTER • ONLINE", status=200)

async def start_web_server():
    try:
        app = web.Application()
        app.router.add_get("/", handle_ping)
        app.router.add_get("/health", handle_ping)
        runner = web.AppRunner(app)
        await runner.setup()
        port = int(os.environ.get("PORT", 8080))
        site = web.TCPSite(runner, "0.0.0.0", port)
        await site.start()
        print(f"Web server bound to port {port} for Cloud Hosting.")
    except OSError:
        print("Port already in use, skipping port bind.")
    except Exception as e:
        print(f"Web server initialization failed: {e}")

# ============================================================
#               SYSTEM STARTUP & AUTO-RELOAD
# ============================================================

async def restore_media_from_db():
    try:
        doc = await settings_col.find_one({"key": "welcome_media_data"})
        if doc and "data" in doc:
            m_type = doc.get("type", "photo")
            file_path = PHOTO_CACHE_PATH if m_type == "photo" else VIDEO_CACHE_PATH
            with open(file_path, "wb") as f:
                f.write(doc["data"])
            CACHED_MEDIA["type"] = m_type
            CACHED_MEDIA["path"] = file_path
            print(f"Restored welcome {m_type} from MongoDB backup.")
    except Exception as e:
        print(f"[Media Restore Error]: {e}")
        await send_error_log(e, context="restore_media_from_db")

async def keep_client_alive(cl: TelegramClient, uid: int):
    while True:
        try:
            if not cl.is_connected():
                await cl.connect()
            await cl.run_until_disconnected()
        except asyncio.CancelledError:
            break
        except Exception as e:
            print(f"[Userbot {uid} Reconnecting...]: {e}")
            await send_error_log(e, context=f"keep_client_alive (User {uid})")
            await asyncio.sleep(5)

async def load_saved_sessions():
    count = 0
    try:
        cursor = sessions_col.find({})
        async for row in cursor:
            uid = row["user_id"]
            s_str = row["session"]
            cl = None
            try:
                cl = TelegramClient(StringSession(s_str), API_ID, API_HASH)
                await cl.connect()
                if await cl.is_user_authorized():
                    register_userbot_handlers(cl, uid)
                    active_clients[uid] = cl
                    asyncio.create_task(keep_client_alive(cl, uid))
                    count += 1
                else:
                    await sessions_col.delete_one({"user_id": uid})
                    if cl.is_connected():
                        await cl.disconnect()
            except (AuthKeyDuplicatedError, AuthKeyInvalidError):
                await sessions_col.delete_one({"user_id": uid})
                if cl and cl.is_connected():
                    await cl.disconnect()
                await log_to_channel(f"⚠️ **Session Terminated by Telegram:** User `{uid}` ka session invalid ho chuka hai aur database se hata diya gaya.")
            except Exception as e:
                if cl and cl.is_connected():
                    await cl.disconnect()
                print(f"[Error loading user {uid}]: {e}")
                await send_error_log(e, context=f"load_saved_sessions (Loading User {uid})")
        print(f"Loaded {count} active userbot clients from MongoDB.")
    except Exception as e:
        print(f"[Critical MongoDB Session Load Error]: {e}")
        await send_error_log(e, context="load_saved_sessions (Database Query)")

async def main():
    loop = asyncio.get_running_loop()
    loop.set_exception_handler(global_exception_handler)

    print("=" * 50)
    print("      ASHISH X HOSTER MULTI-USERBOT V5")
    print("=" * 50)

    await start_web_server()

    try:
        await bot.start(bot_token=BOT_TOKEN)
        print("Main Telegram Bot is ONLINE.")
    except Exception as e:
        print(f"[Bot Start Fatal Error]: {e}")
        sys.exit(1)

    try:
        me = await bot.get_me()
        CACHED_BOT_INFO["username"] = me.username or "Ashishxophsjs_bot"
        CACHED_BOT_INFO["display_name"] = me.first_name or "ASHISH BOT"
    except Exception as e:
        await send_error_log(e, context="Get Bot Profile")

    await restore_media_from_db()
    await load_saved_sessions()
    print("All subsystems running perfectly.")

    asyncio.create_task(log_to_channel(f"⚡ **{BRAND} Server Re-deployed & Online!**"))
    await bot.run_until_disconnected()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except (KeyboardInterrupt, SystemExit):
        pass
    except Exception as e:
        print(f"[Fatal Launch Error]: {e}")
