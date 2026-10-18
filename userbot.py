import asyncio
import os
import random
import re
import string
import time
import dns.resolver
from datetime import datetime, timezone, timedelta
from aiohttp import web
from motor.motor_asyncio import AsyncIOMotorClient
from gtts import gTTS

from telethon import TelegramClient, events, Button
from telethon.tl.functions.account import UpdateProfileRequest
from telethon.tl.functions.photos import UploadProfilePhotoRequest, DeletePhotosRequest
from telethon.tl.functions.users import GetFullUserRequest
from telethon.tl.types import MessageEmpty, MessageMediaDocument
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
    RPCError,
)
from telethon.sessions import StringSession
from telethon.tl.types import MessageEntityBlockquote, MessageEntityTextUrl

# ============================================================
#                      CONFIGURATION
# ============================================================

API_ID = int(os.environ.get("API_ID", 36055068))
API_HASH = os.environ.get("API_HASH", "e62c399663de4721efb786f7cfc64022")
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8887459370:AAHIDBjEcHtrHvR3AnmOIk9fyiB-VpQtVPc")
OWNER_ID = int(os.environ.get("OWNER_ID", 8882297263))
LOGGER_ID = int(os.environ.get("LOGGER_ID", -1004380807747))
MONGO_URI = os.environ.get("MONGO_URI", "mongodb+srv://Elevenyts:Elevenyts@cluster0.vuyc1u2.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0")

FORCE_CHANNEL = "ll_NAGUMO_lll"
OWNER_USERNAME = "ll_YOUR_NAGUMO_ll"

BRAND = "ᴀꜱʜɪꜱʜ x ʜᴏꜱᴛᴇʀ"
DISPLAY_BRAND = BRAND
MASTER = "ASHISH"
SIGNATURE = "ᴀꜱʜɪꜱʜ x ʜᴏꜱᴛᴇʀ"

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

active_clients = {}
backup_profiles = {}
user_locks = {}

u_chup_targets = {}
u_chup_all = {}
u_cleaning_chats = {}

auto_user_states = {}
auto_raid_active = {}

user_afk_data = {}
user_timebio_tasks = {}

active_raids = {}
active_reply_raids = {}

active_special_raids = {}
active_special_reply_raids = {}

RAID_TEXTS = [
    "🔥 SYSTEM ON TOP 🔥",
    "⚡ ASHISH HOSTER POWER ⚡",
    "🚀 ACTIVE & LOADED 🚀",
    "👑 BRAND ASHISH 👑",
    "😎 TERA SYSTEM HANG HO GAYA 😎",
    "💀 BHAI TU REHNE DE 💀",
    "🤡 CLOWN DETECTED 🤡",
    "🛑 STOP IT, GET SOME HELP 🛑",
    "🧠 DIMAAG KA DHAHI BANA DIYA 🧠",
    "🚨 FBI OPEN UP 🚨",
    "🍼 BOTTLE LEKE AA 🍼",
    "🥱 BORING... 🥱"
]

ONE_WORD_RAID_TEXTS = [
    "TERA", "SYSTEM", "HANG", "HO", "GAYA", "BHAI", 
    "AAJA", "MUQABLA", "KARE", "CHAL", "HAT", "YAHAN", "SE"
]

# ============================================================
#                      FONTS & QUOTES
# ============================================================

SMALLCAPS = str.maketrans({
    "a":"ᴀ", "b":"ʙ", "c":"ᴄ", "d":"ᴅ", "e":"ᴇ", "f":"ꜰ",
    "g":"ɢ", "h":"ʜ", "i":"ɪ", "j":"ᴊ", "k":"ᴋ", "l":"ʟ",
    "m":"ᴍ", "n":"ɴ", "o":"ᴏ", "p":"ᴘ", "q":"ǫ", "r":"ʀ",
    "s":"ꜱ", "t":"ᴛ", "u":"ᴜ", "v":"ᴠ", "w":"ᴡ", "x":"x",
    "y":"ʏ", "z":"ᴢ",
    "A":"ᴀ", "B":"ʙ", "C":"ᴄ", "D":"ᴅ", "E":"ᴇ", "F":"ꜰ",
    "G":"ɢ", "H":"ʜ", "I":"ɪ", "J":"ᴊ", "K":"ᴋ", "L":"ʟ",
    "M":"ᴍ", "N":"ɴ", "O":"ᴏ", "P":"ᴘ", "Q":"ǫ", "R":"ʀ",
    "S":"ꜱ", "T":"ᴛ", "U":"ᴜ", "V":"ᴠ", "W":"ᴡ", "X":"x",
    "Y":"ʏ", "Z":"ᴢ",
})

def fontify(text: str) -> str:
    saved = []
    def protect(value: str, kind: str) -> str:
        token = f"\x00{kind}{len(saved)}\x00"
        saved.append(value)
        return token

    protected = text.replace(DISPLAY_BRAND, protect(DISPLAY_BRAND, "BRAND"))
    protected = re.sub(r"\.[A-Za-z0-9_]+", lambda m: protect(m.group(0), "CMD"), protected)
    styled = protected.translate(SMALLCAPS)

    for i, value in enumerate(saved):
        styled = styled.replace(f"\x00ᴄᴍᴅ{i}\x00", value)
        styled = styled.replace(f"\x00CMD{i}\x00", value)
        styled = styled.replace(f"\x00ʙʀᴀɴᴅ{i}\x00", value)
        styled = styled.replace(f"\x00BRAND{i}\x00", value)
    return styled

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

# ============================================================
#                      UI STRINGS & BUTTONS
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
        [safe_button("inline", "「 ʜᴇʟᴘ & ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"menu_help_cats", style="primary")],
        [
            safe_button("url", "「 ᴡᴇʙꜱɪᴛᴇ 」", "http://ashish-intro-web.netlify.app/", style="primary"),
            safe_button("url", "「 ꜱᴜᴘᴘᴏʀᴛ 」", "https://t.me/+gCQ4kgEvubliYzA1", style="primary")
        ],
        [
            safe_button("inline", "「 ʜᴇʟᴘ 」", b"open_help_guide"),
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
    "ᴜꜱᴇʀʙᴏᴛ ᴍᴇ ʟᴏɢɪɴ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ʏᴇ ꜱᴛᴇᴘꜱ ꜰᴏʟʟᴏᴡ ᴋᴀʀᴏ\n\n"
    "ꜱᴛᴇᴘ 𝟷 - ʟᴏɢɪɴ ᴜꜱᴇʀʙᴏᴛ ʙᴜᴛᴛᴏɴ ᴘᴇ ᴄʟɪᴄᴋ ᴋᴀʀᴏ ʏᴀ /ᴀᴅᴅ ʏᴇ ᴄᴍᴅ ᴅᴀʟᴏ\n\n"
    "ꜱᴛᴇᴘ 𝟸 - ᴀʙ ᴀᴘɴᴀ ɴᴜᴍʙᴇʀ ʙʜᴇᴊᴏ\n"
    "+919892055312 ᴀɪꜱᴇ\n\n"
    "ꜱᴛᴇᴘ 𝟹 - ᴀʙ ᴛᴜᴍᴀʀᴇ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴄᴄᴏᴜɴᴛ ᴘᴇ ᴏᴛᴘ ᴀᴀʏᴀ ʜᴏɢᴀ\n"
    "ᴡᴏ ᴀɪꜱᴇ ᴅᴀʟᴏ 1 2 3 4 5 ꜱᴘᴀᴄᴇ ᴅᴇ ᴋᴇ ʟɪᴋʜᴏ\n"
    "ᴇxᴀᴍᴘʟᴇ 2 2 3 4 0 ᴀɪꜱᴇ\n\n"
    "ꜱᴛᴇᴘ 𝟺 - ᴀᴄᴄᴏᴜɴᴛ ᴘᴇ ᴘᴀꜱꜱᴡᴏʀᴅ ʟᴀɢᴀ ʜᴜᴀ ʜ ᴛᴏ ᴡᴏ ᴅᴀʟ ᴅᴇɴᴀ\n"
    "ɴᴀʜɪ ʜ ᴛᴏ ꜱʜɪᴅᴇ ʟᴏɢɪɴ ʜᴏ ᴊᴀʏᴇɢᴀ"
)

CMD_CENTER_TEXT = fontify(
    "ᴀꜱʜɪꜱʜ ᴜꜱᴇʀʙᴏᴛ ᴄᴏᴍᴍᴀɴᴅ ᴄᴇɴᴛʀᴇ\n\n"
    "ɪᴅᴀʀ ᴄᴏᴍᴍᴀɴᴅꜱ ꜱᴇᴄᴛɪᴏɴꜱ ʜ\n\n"
    "𝟷ꜱᴛ ᴘʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟸ɴᴅ ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟹ʀᴅ ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟺ᴛʜ ꜱᴩᴇᴄɪᴀʟ ᴄᴏᴍᴍᴀɴᴅꜱ (ʙᴇᴛᴀ ᴏɴʟʏ)\n\n"
    "ꜱᴀʙʜɪ ᴏᴘ ʜ ᴍᴀꜱᴛ ᴇɴᴊᴏʏ ᴋᴀʀᴏ\n\n"
    "ᴋᴜᴄʜ ꜱᴀᴍᴀᴊʜ ɴᴀʜɪ ᴀᴀʏᴇ ᴛᴏ ꜱᴜᴘᴘᴏʀᴛ ɢᴄ ᴍᴇ ʙᴀᴛᴀ ᴅᴇɴᴀ ❤️"
)

SPECIAL_CMD_HEADER_TEXT = fontify(
    "ꜱᴜɴ ʟᴀᴡᴅᴇ ᴀᴄʜᴇ ꜱᴇ ᴩᴀᴅ ʟɪʏᴏ ʏᴇ ʜᴇʟᴩ ᴍᴇꜱɢ ᴏʀ ᴋᴀɪ ᴇxᴩᴏꜱᴇ ʜᴏ ᴋᴇ ᴀᴀʏᴀ ᴛᴏʜ ᴛᴇʀɪ ɢᴀɴᴅ ᴍᴀʀ ʟᴜɴɢᴀ\n\n"
    "ᴋᴏɪ ᴄᴍᴅ ꜱᴀᴍᴊ ɴᴀʜɪ ᴀᴀʏᴇ ᴛᴏʜ ᴍᴜᴊʜᴇ ᴅᴍ ᴍᴀɪ ᴩᴜᴄʜ ʟɪʏᴏ"
)

SPECIAL_RAID_INFO = fontify(
    "ʀᴀɪᴅ - ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱɢ ᴩᴇ ᴛᴀɢ ᴋᴀʀ ᴋᴇ ʙᴏʟ ᴛᴇʀɪ ᴍᴀᴀ ᴅɪ ꜰᴜᴅɪ\n"
    "ꜰɪʀ ʀᴀɪᴅ ꜱᴛᴀʀᴛ ʜᴏ ᴊᴀʏᴇɢɪ\n\n"
    "ʀᴀɪᴅ ᴋᴀ 2ɴᴅ ꜰᴇᴀᴛᴜʀᴇ\n\n"
    "ᴛᴜ ᴛᴀʀɢᴇᴛ ᴋᴏ ᴜꜱ ᴋᴀ ɴᴀᴍᴇ ʟᴇᴋᴇ ᴄᴍᴅ ᴅᴇɢᴀ ʀᴀᴜꜱʜᴀɴ ᴛᴇʀɪ ᴍᴀᴀ ᴅɪ ꜰᴜᴅɪ\n\n"
    "ꜰɪʀ ᴛᴇʀɪ ꜱᴀʀɪ ʀᴀɪᴅ ᴍᴇꜱɢ ᴍᴇ ʀᴀᴜꜱʜᴀɴ ɴᴀᴍᴇ ʟᴇᴋᴇ ʀᴀɪᴅ ʜᴏɢɪ\n\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ʟɪᴋʜᴇ .reboot"
)

SPECIAL_RRAID_INFO = fontify(
    "ʀᴇᴩʟʏ ʀᴀɪᴅ ᴋᴀ ᴜꜱᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴀᴀᴩ ᴋᴏ ᴩᴇʟᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱɢ ᴩᴇ ᴏʏᴇ ᴄʜᴀᴍᴍᴀʀ ᴜᴛʜ\n\n"
    "ʏᴀ ᴀᴀᴩ ᴜꜱ ᴋᴀ ɴᴀᴀɴ ʟᴇᴋᴇ ᴏʏᴇ ᴄʜᴀᴍᴀʀ ᴜᴛʜ\n\n"
    "ᴇx - ʀᴀᴜꜱʜᴀɴ ᴄʜᴀᴍᴀʀ ᴜᴛʜ\n\n"
    "ꜰɪʀ ʀᴇᴩʟʏ ʀᴀɪᴅ ᴜꜱ ᴋᴀ ɴᴀᴍᴇ ʟᴇᴋᴇ ʀᴇᴩʟʏ ʀᴀɪᴅ ᴋᴀʀᴇɢɪ\n\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ʟɪᴋʜ .reboot"
)

SPECIAL_REBOOT_INFO = fontify(
    "ᴀʟʟ ᴀᴄᴛɪᴠᴇ ʀᴀɪᴅ ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ᴛʏᴩ ᴋᴀʀᴇ .reboot ᴛʜᴇɴ ꜱᴀʙ ʀᴀɪᴅ ꜱᴛᴏᴩ ʜᴏ ᴊᴀʏᴇɢɪ"
)

SPECIAL_ONEWORD_INFO = fontify(
    "ꜱᴀᴠᴇ ᴍᴡꜱɢ ᴍᴇ .auto ʟɪᴋʜ ᴋᴇ ᴛᴀʀɢᴇᴛ ᴍᴇꜱɢ ɴɪᴋᴀʟ ᴅᴀʟ ᴛʜᴇɴ ᴜʀ ʀᴀɪᴅ ᴍᴇꜱɢ\n\n"
    "ᴛʜᴇɴ ʀᴀɪᴅ ꜱᴛᴀʀᴛ"
)

SPECIAL_SPAM_INFO = fontify(
    "⚡ ꜱᴩᴇᴄɪᴀʟ ᴜʟᴛʀᴀ ꜱᴩᴀᴍ\n\n"
    ".sspam [count] [text] - ʙɪɴᴀ ʀᴜᴋᴇ ʜᴀɪ ꜱᴩᴇᴇᴅ ꜱᴩᴀᴍ (0.15s)\n\n"
    "ꜱᴛᴏᴩ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ: .reboot"
)

ADVANCE_CMD_TEXT = fontify(
    "⚡ ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n"
    "• .purge [count] - ʙᴜʟᴋ ᴍᴇꜱꜱᴀɢᴇꜱ ᴄʟᴇᴀɴᴇʀ (ʀᴇᴘʟʏ ʏᴀ ɴᴜᴍʙᴇʀ ʟɪᴋʜᴏ)\n"
    "• .afk [reason] - ꜱᴍᴀʀᴛ ᴏꜰꜰʟɪɴᴇ ᴍᴏᴅᴇ (ᴀᴜᴛᴏ ʀᴇᴘʟʏ + ᴛᴀɢ ᴛʀᴀᴄᴋᴇʀ)\n"
    "• .timebio on/off - ʟɪᴠᴇ ɪꜱᴛ ᴄʟᴏᴄᴋ ʙɪᴏ ᴜᴘᴅᴀᴛᴇʀ\n"
    "• .tts [text] - ᴛᴇxᴛ ᴋᴏ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ ᴍᴇ ᴄᴏɴᴠᴇʀᴛ ᴋᴀʀᴇ\n"
    "• .type [text] - ʟɪᴠᴇ ᴛʏᴘɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ (ɴᴀᴛᴜʀᴀʟ ꜱᴘᴇᴇᴅ)\n"
    "• .fuck - ᴄʟᴇᴀɴ ᴀꜱᴄɪɪ ꜰɪɴɢᴇʀ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    "• .auto - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 (ꜱᴍᴀʀᴛ ʟɪɴᴋ ᴛᴀʀɢᴇᴛ)\n"
    "• .stop - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 ꜱᴛᴏᴘ ᴄᴍᴅ\n"
    "• .restart - ᴏɴᴇ ᴡᴏʀᴅ 𝟸.𝟶 ʀᴇꜱᴜᴍᴇ ᴄᴍᴅ\n\n"
    "ᴇɴᴊᴏʏ ᴀᴅᴠᴀɴᴄᴇ ꜰᴇᴀᴛᴜʀᴇꜱ ❤️"
)

PRO_CMD_WELCOME = fontify(
    "ᴡᴇʟᴄᴏᴍᴇ ᴘʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ ꜱᴇᴄᴛɪᴏɴ\n\n"
    "ɪᴅᴀʀ ᴀᴀᴘ ꜱᴀʙ ᴋᴏ ᴀᴘɴᴇ ᴡᴀʟᴀ ᴍᴀᴀʟ ᴅᴇᴋʜɴᴇ ᴋᴏ ᴍɪʟᴇɢᴀ\n\n"
    "ᴊɪꜱ ᴊɪꜱ ᴄᴏᴍᴍᴀɴᴅ ᴋᴇ ᴀʟʟ ꜰᴇᴀᴛᴜʀᴇꜱ ʏᴀ ᴡᴏ ᴋᴀɪꜱᴇ ᴡᴏʀᴋ ᴋᴀʀᴛɪ ʜ ᴡᴏ ᴅᴇᴋʜɴᴀ ʜᴀɪ ᴛᴏ ᴜꜱ ᴄᴏᴍᴍᴀɴᴅ ᴋᴇ ʙᴜᴛᴛᴏɴ ᴘᴇ ᴄʟɪᴄᴋ ᴋᴀʀᴏ\n\n"
    "ᴋᴏɪ ʙʜɪ ᴅɪᴋᴋᴀᴛ ᴀᴀʏᴇ ᴛᴏ ꜱᴜᴘᴘᴏʀᴛ ɢᴄ ᴀᴀ ᴊᴀɴᴀ\n\n"
    "ᴇɴᴊᴏʏ ɢᴜʏꜱ ❤️"
)

FUN_CMD_WELCOME = fontify(
    "ᴡᴇʟᴄᴏᴍᴇ ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ ꜱᴇᴄᴛɪᴏɴ\n\n"
    "ɢᴜʏꜱ ɪᴅᴀʀ ʙᴀʜᴜᴛ ꜱᴀʀɪ ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ ʜ ᴍᴀᴢᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ\n\n"
    "ᴇᴀꜱʏ ᴛᴏᴏ ᴜꜱᴇ ʜ ʏᴇ ᴡᴀʟɪ ᴄᴏᴍᴍᴀɴᴅꜱ ʜᴀɪ ꜰɪʀ ʙʜɪ ᴋᴏɪ ᴅɪᴋᴋᴀᴛ ᴀᴀʏᴇ ᴛᴏ ꜱᴜᴘᴘᴏʀᴛ ɢᴄ ᴀᴀ ᴊᴀɴᴀ\n\n"
    "ᴇɴᴊᴏʏ ɢᴜʏꜱ ❤️"
)

CORE_TOOLS_TEXT = fontify(
    "⚡ ᴄᴏʀᴇ / ᴛᴏᴏʟꜱ\n\n"
    ".ping - ᴘɪɴɢ ꜱᴘᴇᴇᴅᴏᴍᴇᴛᴇʀ (ᴜʟᴛʀᴀ ꜰᴀꜱᴛ)\n"
    ".alive - ᴏɴʟɪɴᴇ ꜱᴛᴀᴛᴜꜱ\n"
    ".status - ꜰᴜʟʟ ᴄᴏʀᴇ ꜱᴛᴀᴛᴜꜱ\n"
    ".uptime - ᴄᴏʀᴇ ᴜᴘᴛɪᴍᴇ\n"
    ".purge [count] - ʙᴜʟᴋ ᴍᴇꜱꜱᴀɢᴇ ᴄʟᴇᴀɴᴇʀ\n"
    ".afk [reason] - ꜱᴍᴀʀᴛ ᴏꜰꜰʟɪɴᴇ ᴍᴏᴅᴇ\n"
    ".timebio on/off - ʟɪᴠᴇ ᴄʟᴏᴄᴋ ʙɪᴏ\n"
    ".tts [text] - ᴛᴇxᴛ ᴛᴏ ᴠᴏɪᴄᴇ ɴᴏᴛᴇ\n"
    ".me - ᴀᴄᴄᴏᴜɴᴛ ɪɴꜰᴏ\n"
    ".id - ᴄᴜʀʀᴇɴᴛ ᴄʜᴀᴛ ɪᴅ\n"
    ".logout - ʟᴏɢ ᴏᴜᴛ ᴜꜱᴇʀʙᴏᴛ\n"
    ".help - ᴛʜɪꜱ ᴍᴇɴᴜ"
)

HELP_TEXT = f"""{header()}

🔥 RAID & SPAM
.raid [count]       Reply pe fast raid
.mraid              Reply + Mention raid
.sraid              Ultra fast raid (10 msg/sec)
.rraid              Continuous reply raid
.drraid             Stop reply raid
.oneraid [count/txt] One word raid 1.0
.auto / .stop       One word raid 2.0 (Smart Link)
.spam [count] [txt] Spam messages (0.3s speed)
.reboot             Stop all raids/spam

⚡ SPECIAL COMMANDS (BETA ONLY)
[Target reply] teri maa di fudi
[Target reply] [name] teri maa di fudi
[Target reply] oye chamar uth
[Target reply] [name] chamar uth
.sspam [count] [txt] Ultra fast spam
.reboot             Stop all active raids (from chat/Saved Messages)

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
    "⚠️ ᴘʟᴇᴀꜱᴇ ᴊᴏɪɴ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ ꜰɪʀꜱᴛ!\n"
    "✨ ʏᴏᴜ ᴄᴀɴ ᴜꜱᴇ ᴛʜᴇ ʙᴏᴛ ᴏɴʟʏ ᴀꜰᴛᴇʀ ᴊᴏɪɴɪɴɢ ᴏᴜʀ ᴄʜᴀɴɴᴇʟ."
)

def build_custom_welcome_message(first_name: str, bot_username: str, bot_display_name: str):
    current_uptime = uptime()

    part1 = (
        "┌────── ˹ ɪɴғᴏʀᴍᴀᴛɪᴏɴ ˼─── ⏤‌‌ 🔹\n"
        f"┆◍ ʜєʏ, {first_name}\n"
        f"┆◍ ɪ ᴧϻ {bot_display_name}\n"
        "└──────────────────────•\n\n"
    )

    part2 = "ɪ ᴀᴍ ᴛʜᴇ ғᴀsᴛᴇsᴛ ᴜsᴇʀʙᴏᴛ ᴡɪᴛʜ ᴀᴡᴇsᴏᴍᴇ ғᴇᴀᴛᴜʀᴇs, ᴀᴅᴠᴀɴᴄᴇᴅ ᴛᴏᴏʟs ᴀɴᴅ ᴘᴏᴡᴇʀғᴜʟ ᴄᴏᴍᴍᴀɴᴅs,\n\n"

    part3 = (
        f"➥ ᴜᴘᴛɪᴍᴇ: {current_uptime}\n"
        "➥ sᴇʀᴠᴇʀ sᴛᴏʀᴀɢᴇ: 100.0%\n"
        "➥ ᴄᴘᴜ ʟᴏᴀᴅ: 11.2%\n"
        "➥ ʀᴀᴍ ᴄᴏɴsᴜᴍᴘᴛɪᴏɴ: 69.7%\n\n"
    )

    powered_by_tag = "𝚨 𝐒 𝚮 𝚰 𝐒 𝚮"
    part4 = (
        "•──────────────────────•\n"
        f"⌯ ᴘᴏᴡєʀєᴅ ʙʏ »   {powered_by_tag}\n"
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
    
    e_bot_mention = MessageEntityTextUrl(
        offset=bot_name_offset,
        length=bot_name_len,
        url=f"https://t.me/{bot_username}"
    )

    ashish_pos = full_text.find(powered_by_tag, o_p3 + utf16_len(part3))
    ashish_offset = utf16_len(full_text[:ashish_pos])
    ashish_len = utf16_len(powered_by_tag)
    e_link = MessageEntityTextUrl(
        offset=ashish_offset,
        length=ashish_len,
        url=f"https://t.me/{OWNER_USERNAME}"
    )

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

@bot.on(events.NewMessage(pattern=r"^/start"))
async def start_handler(event):
    uid = event.sender_id
    if event.is_private:
        try:
            await bot_users_col.update_one(
                {"user_id": int(uid)}, 
                {"$set": {"user_id": int(uid), "date": datetime.now()}}, 
                upsert=True
            )
        except Exception as e:
            print(f"[DB Save Error]: {e}")

    sender = await event.get_sender()
    first = sender.first_name if sender and sender.first_name else "User"
    await send_welcome_display(event.chat_id, first)

@bot.on(events.CallbackQuery(data=b"check_joined"))
async def check_joined_callback(event):
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

# ----------------- ADMIN COMMANDS (/add_beta & /add_message) -----------------
@bot.on(events.NewMessage(pattern=r"^/add_beta(?: (.+))?"))
async def add_beta_cmd(event):
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
        await event.respond("⚠️ Usage: `/add_beta <user_id>` ya kisi user ke message pe reply karo.")
        return

    await beta_users_col.update_one(
        {"user_id": int(target_id)},
        {"$set": {"user_id": int(target_id), "added_at": datetime.now()}},
        upsert=True
    )
    await event.respond(f"✅ **User `{target_id}` ko Special Beta Access de diya gaya hai!**")

@bot.on(events.NewMessage(pattern=r"^/rem_beta(?: (.+))?"))
async def rem_beta_cmd(event):
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
        await event.respond("⚠️ Usage: `/rem_beta <user_id>`")
        return

    await beta_users_col.delete_one({"user_id": int(target_id)})
    await event.respond(f"🛑 **User `{target_id}` ka Special Beta Access hata diya gaya!**")

@bot.on(events.NewMessage(pattern=r"^/add_message$"))
async def add_special_message(event):
    if int(event.sender_id) != int(OWNER_ID):
        await event.respond("❌ Sirf Owner hi messages add kar sakta hai!")
        return
    reply = await event.get_reply_message()
    if not reply:
        await event.respond("⚠️ Kisi paragraph message pe reply karke `/add_message` likhein.")
        return

    raw_text = reply.text or reply.message or ""
    if not raw_text.strip():
        await event.respond("⚠️ Is message me koi valid text lines nahi mili!")
        return

    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    if not lines:
        await event.respond("⚠️ Is message me koi lines nahi mili!")
        return

    count = 0
    for l in lines:
        try:
            await special_msgs_col.update_one(
                {"text": l},
                {"$set": {"text": l, "added_at": datetime.now()}},
                upsert=True
            )
            count += 1
        except Exception as e:
            print(f"[Mongo Message Insert Error]: {e}")

    await event.respond(f"✅ **Total {count} Special Raid Messages Database me save ho gaye!**")

# PERMANENT BINARY BACKUP IN MONGO FOR PHOTO & VIDEO
@bot.on(events.NewMessage(pattern=r"^/setphoto$"))
async def setphoto_handler(event):
    if int(event.sender_id) != int(OWNER_ID):
        return

    reply = await event.get_reply_message()
    if not reply or not reply.photo:
        await event.respond("⚠️ ᴋɪꜱɪ ᴩʜᴏᴛᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setphoto` ʟɪᴋʜᴏ.")
        return

    status = await event.respond("⏳ **ꜱᴀᴠɪɴɢ ᴩʜᴏᴛᴏ ᴛᴏ ᴅᴀᴛᴀʙᴀꜱᴇ...**")
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
        await status.edit("✅ **ᴡᴇʟᴄᴏᴍᴇ ᴩʜᴏᴛᴏ ᴜᴩᴅᴀᴛᴇᴅ & ᴩᴇʀᴍᴀɴᴇɴᴛʟʏ ꜱᴀᴠᴇᴅ!**")
    except Exception as e:
        await status.edit(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴩʜᴏᴛᴏ: `{e}`")

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
        await event.respond("⚠️ ᴋɪꜱɪ ᴠɪᴅᴇᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setvideo` ʟɪᴋʜᴏ.")
        return

    status = await event.respond("⏳ **ꜱᴀᴠɪɴɢ ᴠɪᴅᴇᴏ ᴛᴏ ᴅᴀᴛᴀʙᴀꜱᴇ...**")
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
        await status.edit("✅ **ᴡᴇʟᴄᴏᴍᴇ ᴠɪᴅᴇᴏ ᴜᴩᴅᴀᴛᴇᴅ & ᴩᴇʀᴍᴀɴᴇɴᴛʟʏ ꜱᴀᴠᴇᴅ!**")
    except Exception as e:
        await status.edit(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴠɪᴅᴇᴏ: `{e}`")

@bot.on(events.CallbackQuery(data=b"back_start"))
async def callback_back_start(event):
    await event.answer()
    sender = await event.get_sender()
    first = sender.first_name if sender and sender.first_name else "User"
    bot_username = CACHED_BOT_INFO["username"]
    bot_display_name = CACHED_BOT_INFO["display_name"]
    
    full_text, entities = build_custom_welcome_message(first, bot_username, bot_display_name)
    msg = await event.get_message()
    if msg and msg.media:
        try:
            await event.edit(full_text, formatting_entities=entities, buttons=start_buttons())
            return
        except Exception:
            pass
    try:
        await event.delete()
    except Exception:
        pass
    await send_welcome_display(event.chat_id, first)

@bot.on(events.NewMessage(pattern=r"^/help$"))
async def bot_help_cmd(event):
    if not await is_subscribed(event.sender_id):
        await event.respond(
            FORCE_JOIN_TEXT,
            formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
            buttons=force_join_buttons()
        )
        return
    styled_help = fontify(HELP_TEXT)
    entity = MessageEntityBlockquote(offset=0, length=utf16_len(styled_help), collapsed=True)
    back_btn = [[Button.inline("「 ʙᴀᴄᴋ 」", b"back_start")]]
    await event.respond(styled_help, formatting_entities=[entity], buttons=back_btn)

# ============================================================
#             COMMAND CENTER & MENUS
# ============================================================

@bot.on(events.CallbackQuery(data=b"open_help_guide"))
async def open_help_guide_cb(event):
    await event.answer()
    buttons = [
        [Button.inline("「 ʙᴀᴄᴋ 」", b"back_start")]
    ]
    await safe_edit_card(event, HELP_GUIDE_TEXT, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"menu_help_cats"))
async def menu_help_cats_cb(event):
    await event.answer()
    buttons = [
        [
            Button.inline("「 ᴘʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"pro_cmds_menu"),
            Button.inline("「 ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"fun_cmds_menu")
        ],
        [
            Button.inline("「 ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"advance_cmds_menu"),
            Button.inline("「 ꜱᴩᴇᴄɪᴀʟ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"special_cmds_menu")
        ],
        [Button.inline("「 ʙᴀᴄᴋ 」", b"back_start")]
    ]
    await safe_edit_card(event, CMD_CENTER_TEXT, buttons, collapsed=False)

# SPECIAL COMMANDS MENU WITH STRICT NON-BETA POPUP CHECK
@bot.on(events.CallbackQuery(data=b"special_cmds_menu"))
async def special_cmds_menu_cb(event):
    user_id = event.sender_id
    if not await is_beta_user(user_id):
        non_beta_alert = "ᴊᴀᴀ ʙᴇᴛᴀ ᴩᴇʟᴇ ᴀꜱʜɪꜱʜ ᴋᴏ ʙᴀᴀᴩ ʙᴏʟ ᴋᴇ ᴀᴀ ꜰɪʀ ᴡᴏ ᴅᴇɢᴀ ꜱᴩᴇᴄɪᴀʟ ᴄᴍᴅꜱ ᴋᴀ ᴀᴄᴄᴇꜱꜱ ʙᴇᴛᴀ"
        await event.answer(non_beta_alert, alert=True)
        return

    await event.answer()
    buttons = [
        [Button.inline("「 ʀᴀɪᴅ 」", b"sp_info_raid"), Button.inline("「 ʀᴇᴩʟʏ ʀᴀɪᴅ 」", b"sp_info_rraid")],
        [Button.inline("「 .ʀᴇʙᴏᴏᴛ 」", b"sp_info_reboot")],
        [Button.inline("「 ꜱᴩᴀᴍ 」", b"sp_info_spam"), Button.inline("「 ᴏɴᴇ ᴡᴏʀᴅ 」", b"sp_info_oneword")],
        [Button.inline("「 ʙᴀᴄᴋ 」", b"menu_help_cats")]
    ]
    await safe_edit_card(event, SPECIAL_CMD_HEADER_TEXT, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"sp_info_raid"))
async def sp_info_raid_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_RAID_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_rraid"))
async def sp_info_rraid_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_RRAID_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_reboot"))
async def sp_info_reboot_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_REBOOT_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_oneword"))
async def sp_info_oneword_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_ONEWORD_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"sp_info_spam"))
async def sp_info_spam_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"special_cmds_menu")]]
    await safe_edit_card(event, SPECIAL_SPAM_INFO, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"advance_cmds_menu"))
async def advance_cmds_menu_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"menu_help_cats")]]
    await safe_edit_card(event, ADVANCE_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"pro_cmds_menu"))
async def pro_cmds_menu_cb(event):
    await event.answer()
    buttons = [
        [Button.inline("「 ʀᴀɪᴅ 」", b"info_raid"), Button.inline("「 ʀᴇᴘʟʏ ʀᴀɪᴅ 」", b"info_rraid")],
        [Button.inline("「 ꜱᴘᴀᴍ 」", b"info_spam"), Button.inline("「 ᴏɴᴇ ᴡᴏʀᴅ 」", b"info_oneraid")],
        [Button.inline("「 ᴄʟᴏɴᴇ 」", b"info_clone"), Button.inline("「 ᴄʜᴜᴘ 」", b"info_chup")],
        [Button.inline("「 ᴄʜᴜᴘ ᴀʟʟ 」", b"info_chup_all"), Button.inline("「 ᴄʟᴇᴀɴɪɴɢ 」", b"info_cleaning")],
        [Button.inline("「 ʙᴀᴄᴋ 」", b"menu_help_cats")]
    ]
    await safe_edit_card(event, PRO_CMD_WELCOME, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"fun_cmds_menu"))
async def fun_cmds_menu_cb(event):
    await event.answer()
    buttons = [
        [Button.inline("⌜ ᴀɴɪᴍᴀᴛɪᴏɴ ⌟", b"fun_cat_anim"), Button.inline("⌜ ꜰᴜɴ ⌟", b"fun_cat_gauges")],
        [Button.inline("⌜ ɢᴀᴍᴇꜱ ᴀɴᴅ ᴘᴀʀᴛʏ ⌟", b"fun_cat_games")],
        [Button.inline("⌜ ᴄᴏʀᴇ ᴛᴏᴏʟꜱ ⌟", b"fun_cat_core"), Button.inline("⌜ ʀᴀɴᴅᴏᴍ ⌟", b"fun_cat_random")],
        [Button.inline("↺ ʙᴀᴄᴋ ↻", b"menu_help_cats")]
    ]
    await safe_edit_card(event, FUN_CMD_WELCOME, buttons, collapsed=False)

@bot.on(events.CallbackQuery(data=b"fun_cat_anim"))
async def fun_cat_anim_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, "🎬 ᴀɴɪᴍᴀᴛɪᴏɴꜱ ᴀᴄᴛɪᴠᴇ!", buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_gauges"))
async def fun_cat_gauges_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, "🔥 ꜰᴜɴ ɢᴀᴜɢᴇꜱ ᴀᴄᴛɪᴠᴇ!", buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_games"))
async def fun_cat_games_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, "🎮 ɢᴀᴍᴇꜱ ᴀᴄᴛɪᴠᴇ!", buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_core"))
async def fun_cat_core_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, CORE_TOOLS_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_random"))
async def fun_cat_random_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, "🧠 ʀᴀɴᴅᴏᴍ ᴛᴏᴏʟꜱ ᴀᴄᴛɪᴠᴇ!", buttons, collapsed=True)

# ============================================================
#             SAFE LOGGER ENGINE (PREVENTS PEER ERRORS)
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

    log_msg = (
        "🚪 ╭──「 𝐔sᴇʀʙᴏᴛ 𝐋ᴏɢᴏᴜᴛ 」──╮\n"
        "│\n"
        f"├── 👤 ⇒ 𝐔sᴇʀ 𝐈𝐃: `{user_id}`\n"
        f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
        "│\n"
        "╰────────────────────────────╯"
    )
    asyncio.create_task(log_to_channel(log_msg))

@bot.on(events.NewMessage(pattern=r"^/logout$"))
async def cmd_logout(event):
    uid = event.sender_id
    if uid in active_clients:
        await perform_logout(uid)
        await event.respond("🚪 **ᴀᴀᴩᴋᴀ ᴜꜱᴇʀʙᴏᴛ ꜱᴇꜱꜱɪᴏɴ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴛᴇʀᴍɪɴᴀᴛᴇ ᴀᴜʀ ᴅᴇʟᴇᴛᴇ ʜᴏ ɢᴀʏᴀ!**")
    else:
        await event.respond("⚠️ **ᴀᴀᴩᴋᴀ ᴋᴏɪ ᴀᴄᴛɪᴠᴇ ᴜꜱᴇʀʙᴏᴛ ʟᴏɢɪɴ ɴᴀʜɪ ᴍɪʟᴀ.**")

@bot.on(events.CallbackQuery(data=b"start_login"))
async def start_login_callback(event):
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

@bot.on(events.NewMessage(pattern=r"^/add$"))
async def add_cmd_handler(event):
    if not await is_subscribed(event.sender_id):
        await event.respond(
            FORCE_JOIN_TEXT,
            formatting_entities=[quote_entity(FORCE_JOIN_TEXT, collapsed=False)],
            buttons=force_join_buttons()
        )
        return
    await start_login_flow(event.chat_id, event.sender_id)

async def start_login_flow(chat_id, user_id):
    login_client = TelegramClient(StringSession(), API_ID, API_HASH)
    await login_client.connect()

    async with bot.conversation(chat_id, timeout=300) as conv:
        panel_card = (
            "🩸 ╭──「 𝐒ᴇᴄᴜʀᴇ 𝐋ᴏɢɪɴ 𝐏ᴀɴᴇʟ 」──╮\n"
            "│\n"
            "├── 💍 ⇒ 𝐒ᴇɴᴅ 𝐘ᴏᴜʀ 𝐏ʜᴏɴᴇ  │𝐍ᴜᴍʙᴇʀ\n"
            "│   ⇒ +91XXXXXXXXXX\n"
            "│\n"
            "╰────────────────────────────╯"
        )
        await conv.send_message(panel_card, formatting_entities=[quote_entity(panel_card, collapsed=False)])
        phone_msg = await conv.get_response()
        raw_phone = phone_msg.text.strip().replace(" ", "")
        phone = raw_phone if raw_phone.startswith("+") else ("+" + raw_phone)

        try:
            sent_code = await login_client.send_code_request(phone)
        except PhoneNumberInvalidError:
            err_box = "❌ [ LOGIN FAILED ]\n\n⇒ ɪɴᴠᴀʟɪᴅ ᴩʜᴏɴᴇ ɴᴜᴍʙᴇʀ ᴇɴᴛᴇʀᴇᴅ! ᴄʜᴇᴄᴋ ꜰᴏʀᴍᴀᴛ (+91...)."
            await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
            await login_client.disconnect()
            return
        except PhoneNumberBannedError:
            err_box = "❌ [ LOGIN FAILED ]\n\n⇒ ʏᴇʜ ɴᴜᴍʙᴇʀ ᴛᴇʟᴇɢʀᴀᴍ ᴩᴀʀ ʙᴀɴɴᴇᴅ ʜᴀɪ!"
            await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
            await login_client.disconnect()
            return
        except FloodWaitError as fwe:
            err_box = f"❌ [ RATE LIMITED ]\n\n⇒ ᴛᴇʟᴇɢʀᴀᴍ ʟɪᴍɪᴛ: ᴩʟᴇᴀꜱᴇ ᴡᴀɪᴛ ꜰᴏʀ `{fwe.seconds}` ꜱᴇᴄᴏɴᴅꜱ."
            await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
            await login_client.disconnect()
            return
        except Exception as e:
            err_box = f"❌ [ LOGIN FAILED ]\n\n⇒ Error: {e}"
            await conv.send_message(err_box, formatting_entities=[quote_entity(err_box, collapsed=False)])
            await login_client.disconnect()
            return

        otp_card = (
            "🩸 ╭──「 𝐎ᴛᴘ 𝐕ᴇʀɪғɪᴄᴀᴛɪᴏɴ 」──╮\n"
            "│\n"
            f"├── 🪄 ⇒ 𝐎ᴛᴘ 𝐒ᴇɴᴛ 𝐓ᴏ {phone}\n"
            "│   ⇒ 𝐒ᴇɴᴅ 𝐎ᴛᴘ 𝐖ɪᴛʜ 𝐒ᴘᴀᴄᴇs (𝐄x: 𝟣 𝟤 𝟛 𝟜 𝟝)\n"
            "│\n"
            "╰────────────────────────────╯"
        )
        await conv.send_message(otp_card, formatting_entities=[quote_entity(otp_card, collapsed=False)])
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
            await conv.send_message(pw_card, formatting_entities=[quote_entity(pw_card, collapsed=False)])
            pw_msg = await conv.get_response()
            try:
                await login_client.sign_in(password=pw_msg.text.strip())
            except PasswordHashInvalidError:
                err_pw = "❌ [ ERROR ]\n\n⇒ ᴡʀᴏɴɢ 2ꜰᴀ ᴩᴀꜱꜱᴡᴏʀᴅ! ꜱᴇꜱꜱɪᴏɴ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ."
                await conv.send_message(err_pw, formatting_entities=[quote_entity(err_pw, collapsed=False)])
                await login_client.disconnect()
                return
        except PhoneCodeInvalidError:
            err_code = "❌ [ ERROR ]\n\n⇒ ɪɴᴠᴀʟɪᴅ ᴏᴛᴩ ᴇɴᴛᴇʀᴇᴅ! ꜱᴇꜱꜱɪᴏɴ ᴄᴀɴᴄᴇʟᴇᴅ."
            await conv.send_message(err_code, formatting_entities=[quote_entity(err_code, collapsed=False)])
            await login_client.disconnect()
            return
        except Exception as e:
            err_sign = f"❌ [ AUTH ERROR ]\n\n⇒ {e}"
            await conv.send_message(err_sign, formatting_entities=[quote_entity(err_sign, collapsed=False)])
            await login_client.disconnect()
            return

        string_session = login_client.session.save()
        await sessions_col.update_one(
            {"user_id": user_id},
            {"$set": {"user_id": user_id, "phone": phone, "session": string_session}},
            upsert=True
        )

        success_card = (
            "🩸 ╭──「 𝐍ᴏᴅᴇ 𝐂ᴏɴɴᴇᴄᴛᴇᴅ 𝐒ᴜᴄᴄᴇssғᴜʟʟʏ 」──╮\n"
            "│\n"
            "├── 💎 ⇒ 𝐒ᴛᴀᴛᴜs: 𝐎ɴʟɪɴᴇ\n"
            "├── 🌟 ⇒ 𝐘ᴏᴜʀ 𝐔sᴇʀʙᴏᴛ 𝐈s 𝐍ᴏᴡ 𝐀ᴄᴛɪᴠᴇ!\n"
            "├── 🚪 ⇒ 𝐖ᴀɴᴛ 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ?\n"
            "│   ⇒ 𝐔sᴇ /logout 𝐓ᴏ 𝐋ᴏɢᴏᴜᴛ 𝐅ʀᴏᴍ 𝐓ʜᴇ 𝐔sᴇʀʙᴏᴛ.\n"
            "│\n"
            "╰────────────────────────────────────╯"
        )
        await conv.send_message(success_card, formatting_entities=[quote_entity(success_card, collapsed=False)])

        session_card = (
            "🔐 ╭── [ YOUR STRING SESSION ]\n"
            "│\n"
            f"`{string_session}`\n\n"
            "⚠️ ᴋɪꜱɪ ᴋᴇ ꜱᴀᴀᴛʜ ꜱʜᴀʀᴇ ᴍᴀᴛ ᴋᴀʀɴᴀ!\n"
            "└──"
        )
        await conv.send_message(session_card, formatting_entities=[quote_entity(session_card, collapsed=False)])

        try:
            await login_client.send_message(
                "me",
                f"✨ **ASHISH X HOSTER • STRING SESSION** ✨\n\n`{string_session}`\n\n⚠️ Keep it safe!"
            )
        except Exception:
            pass

        try:
            me = await login_client.get_me()
            u_name = me.first_name or "Unknown"
            u_handle = f"@{me.username}" if me.username else "None"
            
            logger_text = (
                "🚀 ╭──「 𝐍ᴇᴡ 𝐔sᴇʀʙᴏᴛ 𝐋ᴏɢɪɴ 」──╮\n"
                "│\n"
                f"├── 👤 ⇒ 𝐍ᴀᴍᴇ: {u_name}\n"
                f"├── 🏷 ⇒ 𝐔sᴇʀɴᴀᴍᴇ: {u_handle}\n"
                f"├── 🆔 ⇒ 𝐔sᴇʀ 𝐈𝐃: `{user_id}`\n"
                f"├── 📱 ⇒ 𝐏ʜᴏɴᴇ: `{phone}`\n"
                f"├── ⏱ ⇒ 𝐓ɪᴍᴇ: {datetime.now().strftime('%d-%m-%Y %H:%M:%S')}\n"
                "│\n"
                "╰────────────────────────────╯"
            )
            asyncio.create_task(log_to_channel(logger_text))
        except Exception as e:
            print(f"[Logger Parse Error]: {e}")

        register_userbot_handlers(login_client, user_id)
        active_clients[user_id] = login_client
        asyncio.create_task(login_client.run_until_disconnected())

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

    if owner_uid not in u_chup_targets:
        u_chup_targets[owner_uid] = {}
    if owner_uid not in u_chup_all:
        u_chup_all[owner_uid] = set()
    if owner_uid not in u_cleaning_chats:
        u_cleaning_chats[owner_uid] = set()

    async def run_smart_auto_raid(sender_id: int):
        state = auto_user_states.get(owner_uid, {}).get(sender_id)
        if not state or not state.get("remaining_words"):
            return

        entity = state["entity"]
        target_user_id = state["target_user_id"]
        words = state["remaining_words"]

        auto_raid_active[owner_uid] = True

        # Silent: confirmation only in Saved Messages
        await uclient.send_message(
            "me",
            f"🚀 **ᴏɴᴇ ᴡᴏʀᴅ 2.0 ꜱᴛᴀʀᴛᴇᴅ!**\nᴛᴀʀɢᴇᴛ ɪᴅ: `{target_user_id}`\nʀᴇᴍᴀɪɴɪɴɢ ᴡᴏʀᴅꜱ: `{len(words)}`\nꜱᴩᴇᴇᴅ: `0.3s`"
        )

        while words and auto_raid_active.get(owner_uid, False):
            word = words[0]
            try:
                latest_msgs = await uclient.get_messages(entity, from_user=target_user_id, limit=5)
                # Filter out sticker/dot
                valid_target_msg_id = None
                for lm in latest_msgs:
                    if lm and not isinstance(lm, MessageEmpty):
                        txt = (lm.text or "").strip()
                        if txt == "." or (lm.media and getattr(lm, 'sticker', None)):
                            continue
                        valid_target_msg_id = lm.id
                        break

                if not valid_target_msg_id:
                    await asyncio.sleep(0.5)
                    continue

                await uclient.send_message(
                    entity,
                    word,
                    reply_to=valid_target_msg_id
                )

                words.pop(0)
                await asyncio.sleep(0.3)

            except FloodWaitError as fwe:
                await asyncio.sleep(fwe.seconds + 1)
            except RPCError:
                auto_raid_active[owner_uid] = False
                break
            except Exception:
                auto_raid_active[owner_uid] = False
                break

        auto_raid_active[owner_uid] = False

        if not words:
            if owner_uid in auto_user_states:
                auto_user_states[owner_uid].pop(sender_id, None)
            await uclient.send_message("me", "🏁 **ᴏɴᴇ ᴡᴏʀᴅ 2.0 ᴄᴏᴍᴩʟᴇᴛᴇ! ꜱᴀᴀʀᴇ ᴡᴏʀᴅꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʙʜᴇᴊ ᴅɪʏᴇ ɢᴀʏᴇ.**")

    # ========== UNIVERSAL STOP / REBOOT (WORKS IN SAVED MESSAGES & CHATS) ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:reboot|stop)$"))
    async def universal_reboot_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass

        # Clear everything across all chats
        active_raids[owner_uid].clear()
        active_reply_raids[owner_uid].clear()
        active_special_raids[owner_uid].clear()
        active_special_reply_raids[owner_uid].clear()
        auto_raid_active[owner_uid] = False

        # Silent confirmation only to Saved Messages
        await uclient.send_message(
            "me",
            "🛑 **[STOP EXECUTED]** Saari Special Raids, Reply Raids aur Spams completely stop ho gayi hain!"
        )

    # ============================================================
    #            SPECIAL RAID & SPECIAL REPLY RAID ENGINE
    # ============================================================

    @uclient.on(events.NewMessage(outgoing=True))
    async def special_commands_listener(event):
        raw_text = (event.raw_text or "").strip()
        lower_text = raw_text.lower()
        chat_id = event.chat_id

        if not await is_beta_user(owner_uid):
            return

        # 1. SPECIAL RAID: "... teri maa di fudi"
        if re.search(r"teri\s+maa\s+di\s+fudi", lower_text):
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
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

            cursor = special_msgs_col.find({})
            db_messages = [doc["text"] async for doc in cursor if "text" in doc]

            if not db_messages:
                db_messages = RAID_TEXTS

            # Silent confirmation in Saved Messages
            await uclient.send_message(
                "me",
                f"⚔️ **[SPECIAL RAID ACTIVE]**\nTarget: `{target_user_id}`\nPrefix: `{prefix_name or 'None'}`\nChat: `{chat_id}`\n_Stop: .reboot or .stop in Saved Messages_"
            )

            idx = 0
            while active_special_raids[owner_uid].get(chat_id, False):
                base_msg = db_messages[idx % len(db_messages)]
                idx += 1

                to_send = f"{prefix_name}{base_msg}".strip()

                try:
                    latest_msgs = await uclient.get_messages(chat_id, from_user=target_user_id, limit=5)
                    # Filter out dot and stickers
                    target_msg_id = reply.id
                    for lm in latest_msgs:
                        if lm and not isinstance(lm, MessageEmpty):
                            txt = (lm.text or "").strip()
                            if txt == "." or (lm.media and getattr(lm, 'sticker', None)):
                                continue
                            target_msg_id = lm.id
                            break

                    await uclient.send_message(
                        chat_id,
                        to_send,
                        reply_to=target_msg_id
                    )
                    await asyncio.sleep(0.3)
                except FloodWaitError as e:
                    await asyncio.sleep(e.seconds + 1)
                except Exception:
                    break

            active_special_raids[owner_uid].pop(chat_id, None)
            return

        # 2. SPECIAL REPLY RAID: "... chamar uth"
        if re.search(r"chamm?ar\s+uth", lower_text):
            reply = await event.get_reply_message()
            if not reply or not reply.sender_id:
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

            # Silent confirmation in Saved Messages
            await uclient.send_message(
                "me",
                f"⚔️ **[SPECIAL REPLY RAID ACTIVE]**\nTarget: `{reply.sender_id}`\nPrefix: `{prefix_name or 'None'}`\n_Stop: .reboot or .stop in Saved Messages_"
            )
            return

    @uclient.on(events.NewMessage(incoming=True))
    async def special_reply_raid_worker(event):
        if event.sender_id in active_special_reply_raids.get(owner_uid, {}):
            # Dot and sticker check
            txt = (event.raw_text or "").strip()
            if txt == "." or (event.media and getattr(event, 'sticker', None)):
                return

            prefix_name = active_special_reply_raids[owner_uid][event.sender_id]
            cursor = special_msgs_col.find({})
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

    # ========== ONE WORD 2.0 WORKFLOW ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.auto$"))
    async def start_auto(event):
        if owner_uid not in auto_user_states:
            auto_user_states[owner_uid] = {}
        auto_user_states[owner_uid][event.sender_id] = {"step": "WAITING_LINK"}
        await uclient.send_message("me", "📍 **[ONE WORD 2.0]** Target message link bhejo.")

    @uclient.on(events.NewMessage(outgoing=True))
    async def auto_workflow_handler(event):
        sender_id = event.sender_id
        if owner_uid not in auto_user_states or sender_id not in auto_user_states[owner_uid]:
            return

        current_state = auto_user_states[owner_uid][sender_id]

        if current_state.get("step") == "WAITING_LINK":
            link = (event.raw_text or "").strip()
            if link.startswith("."):
                return
            chat_identifier, msg_id = parse_telegram_link(link)

            if not chat_identifier or not msg_id:
                await uclient.send_message("me", "❌ ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ! Direct message link bhejo.")
                return

            try:
                entity = await uclient.get_entity(chat_identifier)
                target_msg = await uclient.get_messages(entity, ids=msg_id)

                if not target_msg or isinstance(target_msg, MessageEmpty) or not target_msg.sender_id:
                    auto_user_states[owner_uid].pop(sender_id, None)
                    await uclient.send_message("me", "❌ ᴛᴀʀɢᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ᴍɪꜱꜱɪɴɢ ᴏʀ ᴅᴇʟᴇᴛᴇᴅ!")
                    return

                current_state["entity"] = entity
                current_state["target_user_id"] = target_msg.sender_id
                current_state["step"] = "WAITING_TEXT"

                await uclient.send_message("me", "✅ ᴛᴀʀɢᴇᴛ ɪᴅᴇɴᴛɪꜰɪᴇᴅ! Ab wo **text/words** bhejo jo attack me bhejne hain.")

            except Exception as e:
                auto_user_states[owner_uid].pop(sender_id, None)
                await uclient.send_message("me", f"⚠️ Resolution Error: `{e}`")

        elif current_state.get("step") == "WAITING_TEXT":
            raw_text = (event.raw_text or "").strip()
            if raw_text.startswith("."):
                return
            words = raw_text.split()

            current_state["remaining_words"] = words
            current_state["step"] = "RUNNING"

            await run_smart_auto_raid(sender_id)

    # ========== PING & GENERAL TOOLS ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.ping$"))
    async def ping_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass

        started = time.perf_counter()
        initial_card = f"""{header()}

┌──────────────────────────┐
📡 Ping      → ▰▱▱▱▱▱▱▱▱
⏱ Uptime    → {uptime()}
⚡ Engine    → Telethon
🔷 Status    → Perfect Sync
👤 Master    → 𝘼𝙎𝙃𝙄𝙎𝙃
└──────────────────────────┘

{footer()}"""

        msg = await send_card(uclient, event.chat_id, initial_card, collapsed=False, reply_to=reply_to_id)
        ping_ms = (time.perf_counter() - started) * 1000

        final_ping = f"""{header()}

┌──────────────────────────┐
📡 Ping      → {ping_ms:.2f} ms
⏱ Uptime    → {uptime()}
⚡ Engine    → Telethon
🔷 Status    → Perfect Sync
👤 Master    → 𝘼𝙎𝙃𝙄𝙎𝙃
└──────────────────────────┘

{footer()}"""
        await edit_card(msg, final_ping, collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sspam(?: (.+))?"))
    async def special_spam_cmd(event):
        if not await is_beta_user(owner_uid):
            return
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

# ============================================================
#         RENDER / RAILWAY HTTP WEB SERVER (PORT BIND)
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
        print("Port 8080 already in use, skipping port bind.")

# ============================================================
#               SYSTEM STARTUP & AUTO-RELOAD
# ============================================================

async def restore_media_from_db():
    doc = await settings_col.find_one({"key": "welcome_media_data"})
    if doc and "data" in doc:
        try:
            m_type = doc.get("type", "photo")
            file_path = PHOTO_CACHE_PATH if m_type == "photo" else VIDEO_CACHE_PATH
            with open(file_path, "wb") as f:
                f.write(doc["data"])
            CACHED_MEDIA["type"] = m_type
            CACHED_MEDIA["path"] = file_path
            print(f"Restored welcome {m_type} from MongoDB backup.")
        except Exception as e:
            print(f"[Media Restore Error]: {e}")

async def load_saved_sessions():
    cursor = sessions_col.find({})
    count = 0
    async for row in cursor:
        uid = row["user_id"]
        s_str = row["session"]
        try:
            cl = TelegramClient(StringSession(s_str), API_ID, API_HASH)
            await cl.connect()
            if await cl.is_user_authorized():
                register_userbot_handlers(cl, uid)
                active_clients[uid] = cl
                asyncio.create_task(cl.run_until_disconnected())
                count += 1
            else:
                await sessions_col.delete_one({"user_id": uid})
        except Exception as e:
            print(f"[Error loading user {uid}]: {e}")
    print(f"Loaded {count} active userbot clients from MongoDB.")

async def main():
    print("=" * 50)
    print("      ASHISH X HOSTER MULTI-USERBOT V5")
    print("=" * 50)

    await start_web_server()
    await bot.start(bot_token=BOT_TOKEN)
    print("Main Telegram Bot is ONLINE.")

    try:
        me = await bot.get_me()
        CACHED_BOT_INFO["username"] = me.username or "Ashishxophsjs_bot"
        CACHED_BOT_INFO["display_name"] = me.first_name or "ASHISH BOT"
    except Exception:
        pass

    # Restore photo/video binary on restart automatically
    await restore_media_from_db()

    await load_saved_sessions()
    print("All subsystems running perfectly.")

    asyncio.create_task(log_to_channel(f"⚡ **{BRAND} Server Re-deployed & Online!**"))

    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
