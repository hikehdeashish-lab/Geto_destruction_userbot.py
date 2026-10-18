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
    RPCError,
)
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

# Global memory cache for instant /start response
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
    except Exception as e:
        print(f"[Safe Edit Error]: {e}")
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

def fun_card(title, body):
    return f"{title}\n\n{body}"

def parse_telegram_link(link: str):
    priv_match = re.search(r"t\.me\/c\/(\d+)\/(\d+)", link)
    if priv_match:
        return int("-100" + priv_match.group(1)), int(priv_match.group(2))

    pub_match = re.search(r"t\.me\/([a-zA-Z0-9_]+)\/(\d+)", link)
    if pub_match:
        return pub_match.group(1), int(pub_match.group(2))

    return None, None

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
    "ɪᴅᴀʀ 𝟹 ᴄᴏᴍᴍᴀɴᴅꜱ ꜱᴇᴄᴛɪᴏɴꜱ ʜ\n\n"
    "𝟷ꜱᴛ ᴘʀᴏ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟸ɴᴅ ꜰᴜɴ ᴄᴏᴍᴍᴀɴᴅꜱ\n"
    "𝟹ʀᴅ ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ\n\n"
    "ꜱᴀʙʜɪ ᴏᴘ ʜ ᴍᴀꜱᴛ ᴇɴᴊᴏʏ ᴋᴀʀᴏ\n\n"
    "ᴋᴜᴄʜ ꜱᴀᴍᴀᴊʜ ɴᴀʜɪ ᴀᴀʏᴇ ᴛᴏ ꜱᴜᴘᴘᴏʀᴛ ɢᴄ ᴍᴇ ʙᴀᴛᴀ ᴅᴇɴᴀ ❤️"
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

RAID_CMD_TEXT = fontify(
    "ʀᴀɪᴅ ᴄᴏᴍᴍᴀɴᴅꜱ ᴀɪꜱᴇ ᴜꜱᴇ ᴋᴀʀᴇ\n\n"
    ".raid - ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ʀᴇᴘʟʏ ᴅᴇ ᴋᴇ ʟɪᴋʜᴇ .ʀᴀɪᴅ 10\n"
    "(ᴊɪᴛɴᴇ ɴᴜᴍʙᴇʀ ʟɪᴋʜᴏɢᴇ ᴜᴛɴɪ ʜɪ ʀᴀɪᴅ ʜᴏɢɪ)\n\n"
    ".mraid - ʏᴇ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ᴍᴇɴᴛɪᴏɴ + ʀᴇᴘʟʏ ᴅᴇ ᴋᴇ ʀᴀɪᴅ ᴋᴀʀᴇɢɪ\n\n"
    ".sraid - ᴜʟᴛʀᴀ ꜰᴀꜱᴛ ʀᴀɪᴅ (1 sec me 10 msg)\n\n"
    "ꜱᴛᴏᴘ ᴄᴍᴅ - .reboot"
)

REPLY_RAID_CMD_TEXT = fontify(
    ".rraid - ʀᴇᴘʟʏ ʀᴀɪᴅ ᴋᴀ ᴜꜱᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ʀᴇᴘʟʏ ᴅᴇ ᴋᴇ ʟɪᴋʜᴇ .ʀʀᴀɪᴅ\n\n"
    "ꜱᴛᴏᴘ ᴄᴍᴅ - .reboot"
)

SPAM_CMD_TEXT = fontify(
    "ꜱᴘᴀᴍ ᴄᴍᴅ ᴜꜱᴇ ᴀɪꜱᴇ ᴋᴀʀᴛᴇ ʜ (ꜱᴘᴇᴇᴅ: 0.3ꜱ)\n\n"
    ".spam 10 (ᴊɪᴛɴᴇ ɴᴜᴍʙᴇʀ ʟɪᴋʜᴏɢᴇ ᴜᴛɴᴀ ꜱᴘᴀᴍ ʜᴏɢᴀ) ᴛᴇxᴛ (ᴊᴏ ᴍᴇꜱꜱᴀɢᴇ ꜱᴘᴀᴍ ᴋᴀʀɴᴀ ʜ ᴡᴏ ʟɪᴋʜᴇ ʏᴀʜᴀ)\n\n"
    "ᴇxᴀᴍᴘʟᴇ - .spam 10 ʜʏ\n\n"
    "ꜱᴛᴏᴘ ᴄᴍᴅ - .reboot"
)

ONE_WORD_CMD_TEXT = fontify(
    "⚡ ᴏɴᴇ ᴡᴏʀᴅ 1.0\n"
    ".oneraid 10 - ɪᴅᴀʀ ᴊɪᴛɴᴇ ɴᴜᴍʙᴇʀ ʟɪᴋʜᴏɢᴇ ᴜᴛɴɪ ᴏɴᴇ ᴡᴏʀᴅ ʀᴀɪᴅ ʜᴏɢɪ\n"
    ".oneraid ᴛᴇxᴛ - ʙɪɴᴀ ɴᴜᴍʙᴇʀ ᴅᴀʟᴇ .oneraid + ᴍᴇꜱꜱᴀɢᴇ ᴏɴᴇ ᴡᴏʀᴅ ᴍᴇ ᴊᴀʏᴇɢᴀ\n\n"
    "━━━━━━━━━━━━━━━━━━━\n"
    "🔥 ᴏɴᴇ ᴡᴏʀᴅ 2.0 (ꜱᴍᴀʀᴛ ᴛᴀʀɢᴇᴛ)\n\n"
    "ᴏɴᴇ ᴡᴏʀᴅ\n"
    "ꜱᴀᴠᴇ ᴍᴇꜱɢ ᴍᴇ ʟɪᴋʜᴏ .auto\n"
    "ꜰɪʀ ᴀᴩɴᴇ ᴛᴀʀɢᴇᴛ ᴋɪ ᴍᴇꜱɢ ʟɪɴᴋ ᴅᴏ ᴊɪꜱ ɢᴄ ᴍᴇ ᴛᴜᴍʜᴇ ᴏɴᴇ ᴡᴏʀᴅ ᴋᴀʀɴᴀ ʜ ꜰɪʀ ᴀᴩɴᴀ ᴏɴᴇ ᴡᴏʀᴅ ᴍᴇꜱɢ ʟɪᴋʜ ᴅᴇɴᴀ\n\n"
    "ꜱᴛᴏᴩ ᴄᴍᴅ - .stop\n"
    "ʀᴇꜱᴜᴍᴇ ᴄᴍᴅ - .restart"
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

FUN_GAUGES_TEXT = fontify(
    "🔥 ꜰᴜɴ & ᴅᴇꜱɪ ɢᴀᴜɢᴇꜱ\n\n"
    ".roast - ꜰᴜɴɴʏ ʀᴏᴀꜱᴛ\n"
    ".love ɴᴀᴍᴇ - ʟᴏᴠᴇ ꜱᴄᴀɴɴᴇʀ\n"
    ".crush - ᴄʀᴜꜱʜ ᴅᴇᴛᴇᴄᴛᴏʀ\n"
    ".marry ɴᴀᴍᴇ - ᴍᴀʀʀɪᴀɢᴇ ꜱᴄᴀɴɴᴇʀ\n"
    ".friend - ꜰʀɪᴇɴᴅꜱʜɪᴘ ᴍᴇᴛᴇʀ\n"
    ".dost - ᴊɪɢʀɪ ʏᴀᴀʀ ᴄʜᴇᴄᴋ\n"
    ".iq ɴᴀᴍᴇ - ʙʀᴀɪɴᴘᴏᴡᴇʀ ꜱᴄᴀɴ\n"
    ".crime - ꜰᴀᴋᴇ ᴘᴏʟɪᴄᴇ ʀᴇᴄᴏʀᴅ\n"
    ".future - 5-ʏᴇᴀʀ ᴄᴀʀᴇᴇʀ ᴘʀᴇᴅɪᴄᴛɪᴏɴ\n"
    ".gf - ɢꜰ ᴄᴏᴜɴᴛᴇʀ ꜱᴄᴀɴ\n"
    ".aukaat ɴᴀᴍᴇ - ʙᴀɴᴋ ʙᴀʟᴀɴᴄᴇ\n"
    ".nalla ɴᴀᴍᴇ - ʙᴇʀᴏᴢɢᴀʀɪ ᴍᴇᴛᴇʀ\n"
    ".shadi - ꜱʜᴀᴅɪ ʙᴀɴᴅ-ʙᴀᴀᴊᴀ ꜱᴄᴀɴ\n"
    ".bhabhi - ʙʜᴀʙʜɪ ʀᴀᴅᴀʀ\n"
    ".gyan ɴᴀᴍᴇ - ᴜɴꜱᴏʟɪᴄɪᴛᴇᴅ ɢʏᴀɴ\n"
    ".acting ɴᴀᴍᴇ - ᴏᴠᴇʀᴀᴄᴛɪɴɢ ᴍᴇᴛᴇʀ\n"
    ".kismat - ʟᴜᴄᴋ/ʙᴀᴅʟᴜᴄᴋ ꜱᴄᴏʀᴇ\n"
    ".pappu ɴᴀᴍᴇ - ᴍᴀꜱᴏᴏᴍɪʏᴀᴛ ꜱᴄᴀɴ\n"
    ".bhagode - ɢʀᴏᴜᴘ ʟᴜʀᴋᴇʀ ᴄʜᴇᴄᴋ\n"
    ".system ɴᴀᴍᴇ - ꜱʏꜱᴛᴇᴍ ʜᴀɴɢ ᴄʜᴇᴄᴋ\n"
    ".chugli ɴᴀᴍᴇ - ᴄʜᴜɢʟɪ ʀᴀᴅᴀʀ\n"
    ".fake ɴᴀᴍᴇ - ꜰᴀᴋᴇ ʀᴀᴇᴇꜱ ꜱᴄᴀɴɴᴇʀ\n"
    ".bewakoof ɴᴀᴍᴇ - ᴅɪᴍᴀɢ ᴄᴀᴘᴀᴄɪᴛʏ\n"
    ".bhaukaal ɴᴀᴍᴇ - ʟᴏᴄᴀʟ ᴅᴏɴ ᴄʜᴇᴄᴋ\n"
    ".aura - ᴀᴜʀᴀ ꜱᴄᴏʀᴇ\n"
    ".sigma - ꜱɪɢᴍᴀ ꜱᴄᴏʀᴇ\n"
    ".sus - ꜱᴜꜱᴘɪᴄɪᴏɴ ᴍᴇᴛᴇʀ\n"
    ".evil - ᴇᴠɪʟ ᴍᴇᴛᴇʀ\n"
    ".rank - ʀᴀɴᴅᴏᴍ ʀᴀɴᴋ\n"
    ".mood - ʀᴀɴᴅᴏᴍ ᴍᴏᴏᴅ\n"
    ".rate ᴛᴇxᴛ - ʀᴀᴛᴇ ᴀɴʏᴛʜɪɴɢ\n"
    ".luck - ʟᴜᴄᴋ ᴘᴇʀᴄᴇɴᴛᴀɢᴇ\n"
    ".predict - ʀᴀɴᴅᴏᴍ ᴘʀᴇᴅɪᴄᴛɪᴏɴ\n"
    ".8ball ǫ - ᴍᴀɢɪᴄ 8-ʙᴀʟʟ\n"
    ".choose ᴀ|ʙ|ᴄ - ʀᴀɴᴅᴏᴍ ᴄʜᴏɪᴄᴇ"
)

HEAVY_ANIMATIONS_TEXT = fontify(
    "🎬 ʜᴇᴀᴠʏ ᴀɴɪᴍᴀᴛɪᴏɴꜱ\n\n"
    ".type [text] - ʟɪᴠᴇ ᴛʏᴘɪɴɢ ᴇғғᴇᴄᴛ\n"
    ".fuck - ꜰᴜᴄᴋ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    ".moye - ᴍᴏʏᴇ ᴍᴏʏᴇ ʙʀᴇᴀᴋᴅᴏᴡɴ\n"
    ".fbi - ꜰʙɪ ꜱᴡᴀᴛ ʀᴀɪᴅ ꜱᴄᴇɴᴇ\n"
    ".gadi - ᴛʜᴀʀ ᴅʀɪꜰᴛ ꜱʏꜱᴛᴇᴍ ᴇɴᴛʀʏ\n"
    ".thanos - ɢᴀᴜɴᴛʟᴇᴛ ꜱɴᴀᴘ & ᴅᴜꜱᴛ\n"
    ".burn - ʙᴜʀɴᴏʟ ᴅɪꜱᴘᴀᴛᴄʜ ᴋɪᴛ\n"
    ".crying - ᴀɴɪᴍᴇ ᴛᴇᴀʀꜱ ꜰʟᴏᴏᴅ\n"
    ".snitch - ꜱᴇᴄʀᴇᴛ ᴄᴀᴍᴇʀᴀ ꜱᴄᴀɴ\n"
    ".fight - ᴀɴɪᴍᴇ ʙᴏxɪɴɢ ᴋ.O.\n"
    ".thappad - ꜰʟʏɪɴɢ ᴄʜᴀᴘᴘᴀʟ ꜱᴛʀɪᴋᴇ\n"
    ".rip - ꜰᴜɴᴇʀᴀʟ ᴄᴏꜰꜰɪɴ ᴅᴀɴᴄᴇ\n"
    ".binod - ʙɪɴᴏᴅ ᴇɴᴄʀʏᴘᴛɪᴏɴ\n"
    ".chai - ᴄᴜᴛᴛɪɴɢ ᴛᴀᴘʀɪ ᴄʜᴀɪ\n"
    ".ghost - ᴍɪᴅɴɪɢʜᴛ ʙʜᴏᴏᴛ ᴘʀᴀɴᴋ\n"
    ".bomb - ᴅᴇꜰᴜꜱᴇ ᴛɪᴍᴇ ʙᴏᴍʙ\n"
    ".heart - ᴘᴜʟꜱɪɴɢ ᴄᴏʟᴏʀꜱ\n"
    ".loading - ᴄʏʙᴇʀ ʟᴏᴀᴅ ʙᴀʀ\n"
    ".slap - ᴍᴇᴍᴇ ꜱʟᴀᴘ ᴀɴɪᴍᴀᴛɪᴏɴ\n"
    ".coffee - ᴄᴏꜰꜰᴇᴇ ʙʀᴇᴡɪɴɢ\n"
    ".scan - ꜱᴀꜰᴇ ᴅɪᴀɢɴᴏꜱᴛɪᴄ\n"
    ".launch - ʀᴏᴄᴋᴇᴛ ᴏʀʙɪᴛ\n"
    ".matrix - ᴄʏʙᴇʀ ꜱᴛʀᴇᴀᴍ\n"
    ".hack - ʜᴀʀᴍʟᴇꜱꜱ ᴛᴇʀᴍɪɴᴀʟ"
)

GAMES_TOOLS_TEXT = fontify(
    "🎮 ɢᴀᴍᴇꜱ & ᴛᴏᴏʟꜱ\n\n"
    ".truth - ᴘᴀʀᴛʏ ᴛʀᴜᴛʜ\n"
    ".toss - ᴄʀɪᴄᴋᴇᴛ ᴛᴏꜱꜱ\n"
    ".dice - ʀᴏʟʟ ᴀ ᴅɪᴄᴇ\n"
    ".flip / .coin - ʜᴇᴀᴅꜱ ᴏʀ ᴛᴀɪʟꜱ\n"
    ".rps - ʀᴏᴄᴋ ᴘᴀᴘᴇʀ ꜱᴄɪꜱꜱᴏʀꜱ\n"
    ".slot - ᴄᴀꜱɪɴᴏ ꜱʟᴏᴛ ᴍᴀᴄʜɪɴᴇ\n"
    ".number - ʟᴜᴄᴋʏ ɴᴜᴍʙᴇʀ\n"
    ".guess - ɴᴜᴍʙᴇʀ ᴄʜᴀʟʟᴇɴɢᴇ\n"
    ".trivia - ᴍɪɴɪ ᴛʀɪᴠɪᴀ\n"
    ".animal - ʀᴀɴᴅᴏᴍ ᴀɴɪᴍᴀʟ\n"
    ".bill - ꜰᴀᴋᴇ ʀᴇꜱᴛᴀᴜʀᴀɴᴛ ʙɪʟʟ\n"
    ".kutai ɴᴀᴍᴇ - ᴅɪɢɪᴛᴀʟ ᴅʜᴜʟᴀɪ ᴍᴀᴄʜɪɴᴇ\n"
    ".shayari - ꜰᴜɴɴʏ ꜱʜᴀʏᴀʀɪ ʟɪɴᴇ\n"
    ".insult ɴᴀᴍᴇ - ꜱᴀᴠᴀɢᴇ ɪɴꜱᴜʟᴛ ʟɪɴᴇ\n"
    ".pass - ꜱᴇᴄᴜʀᴇ ᴘᴀꜱꜱᴡᴏʀᴅ\n"
    ".breakdown ᴛᴇxᴛ - ʟɪɴᴇ-ʙʏ-ʟɪɴᴇ ꜰᴏʀᴍᴀᴛ"
)

RANDOM_SECTION_TEXT = fontify(
    "🧠 ʀᴀɴᴅᴏᴍ\n\n"
    ".joke - ʀᴀɴᴅᴏᴍ ᴊᴏᴋᴇ\n"
    ".fact - ʀᴀɴᴅᴏᴍ ꜰᴀᴄᴛ\n"
    ".quote - ʀᴀɴᴅᴏᴍ ǫᴜᴏᴛᴇ\n"
    ".pick - ʀᴀɴᴅᴏᴍ ᴄᴏʟᴏʀ"
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

{FUN_GAUGES_TEXT}

{HEAVY_ANIMATIONS_TEXT}

{GAMES_TOOLS_TEXT}

{RANDOM_SECTION_TEXT}

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
    
    # Instant memory cache check (No DB delay)
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
        # Fire and forget DB update to keep /start instant
        asyncio.create_task(bot_users_col.update_one(
            {"user_id": int(uid)}, 
            {"$set": {"user_id": int(uid), "date": datetime.now()}}, 
            upsert=True
        ))

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

@bot.on(events.NewMessage(pattern=r"^/setphoto$"))
async def setphoto_handler(event):
    if event.sender_id != OWNER_ID:
        return

    reply = await event.get_reply_message()
    if not reply or not reply.photo:
        await event.respond("⚠️ ᴋɪꜱɪ ᴩʜᴏᴛᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setphoto` ʟɪᴋʜᴏ.")
        return

    status = await event.respond("⏳ **ꜱᴀᴠɪɴɢ ᴩʜᴏᴛᴏ...**")
    try:
        await reply.download_media(file=PHOTO_CACHE_PATH)
        if os.path.exists(VIDEO_CACHE_PATH):
            os.remove(VIDEO_CACHE_PATH)

        CACHED_MEDIA["type"] = "photo"
        CACHED_MEDIA["path"] = PHOTO_CACHE_PATH

        await settings_col.update_one(
            {"key": "welcome_media_id"},
            {"$set": {"key": "welcome_media_id", "type": "photo"}},
            upsert=True
        )
        await status.edit("✅ **ᴡᴇʟᴄᴏᴍᴇ ᴩʜᴏᴛᴏ ᴜᴩᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**")
    except Exception as e:
        await status.edit(f"❌ ꜰᴀɪʟᴇᴅ ᴛᴏ ꜱᴇᴛ ᴩʜᴏᴛᴏ: `{e}`")

@bot.on(events.NewMessage(pattern=r"^/setvideo$"))
async def setvideo_handler(event):
    if event.sender_id != OWNER_ID:
        return

    reply = await event.get_reply_message()
    if not reply or not reply.video:
        await event.respond("⚠️ ᴋɪꜱɪ ᴠɪᴅᴇᴏ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/setvideo` ʟɪᴋʜᴏ.")
        return

    status = await event.respond("⏳ **ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ ᴀɴᴅ ꜱᴀᴠɪɴɢ ᴠɪᴅᴇᴏ...**")
    try:
        await reply.download_media(file=VIDEO_CACHE_PATH)
        if os.path.exists(PHOTO_CACHE_PATH):
            os.remove(PHOTO_CACHE_PATH)

        CACHED_MEDIA["type"] = "video"
        CACHED_MEDIA["path"] = VIDEO_CACHE_PATH

        await settings_col.update_one(
            {"key": "welcome_media_id"},
            {"$set": {"key": "welcome_media_id", "type": "video"}},
            upsert=True
        )
        await status.edit("✅ **ᴡᴇʟᴄᴏᴍᴇ ᴠɪᴅᴇᴏ ᴜᴩᴅᴀᴛᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ!**")
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
            Button.inline("「 ᴀᴅᴠᴀɴᴄᴇ ᴄᴏᴍᴍᴀɴᴅꜱ 」", b"advance_cmds_menu")
        ],
        [Button.inline("「 ʙᴀᴄᴋ 」", b"back_start")]
    ]
    await safe_edit_card(event, CMD_CENTER_TEXT, buttons, collapsed=False)

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

@bot.on(events.CallbackQuery(data=b"info_raid"))
async def info_raid_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, RAID_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_rraid"))
async def info_rraid_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, REPLY_RAID_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_spam"))
async def info_spam_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, SPAM_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_oneraid"))
async def info_oneraid_cb(event):
    await event.answer()
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, ONE_WORD_CMD_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_clone"))
async def info_clone_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʟᴏɴᴇ -  .ᴄʟᴏɴᴇ ʏᴇ ᴄᴍᴅ ᴜꜱᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋɪꜱɪ ʙʜɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ʀᴇᴘʟʏ ᴅᴇ ᴋᴇ .ᴄʟᴏɴᴇ ʟɪᴋʜᴏ\n\n"
        "ᴄʟᴏɴᴇ ʜᴀᴛᴀɴᴇ ᴋᴇ ʟɪʏᴇ\n"
        ".ʙᴀᴄᴋ"
    )
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_chup"))
async def info_chup_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʜᴜᴘ - ɪꜱ ᴄᴍᴅ ᴋᴀ ᴜꜱᴇ ᴋᴀʀ ᴋᴇ ᴛᴜᴍ ᴀᴅᴍɪɴ ᴋᴏ ʙʜɪ ᴍᴜᴛᴇ ᴋᴀʀ ꜱᴀᴋᴛᴇ ʜᴏ\n\n"
        "ᴄʜᴜᴘ - ᴋɪꜱɪ ʙʜɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴘᴇ ʀᴇᴘʟʏ ᴅᴇ ᴋᴇ .ᴄʜᴜᴘ ʟɪᴋʜᴏ\n\n"
        ".ʙᴏʟ - ɪꜱ ꜱᴇ ᴡᴏ ᴜɴᴍᴜᴛᴇ ʜᴏ ᴊᴀʏᴇɢᴀ"
    )
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_chup_all"))
async def info_chup_all_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʜᴜᴘ ᴀʟʟ - ɪꜱ ᴄᴍᴅ ꜱᴇ ᴛᴜᴍ ᴘᴜʀɪ ɢᴄ ᴋᴏ ᴍᴜᴛᴇ ᴋᴀʀ ꜱᴀᴋᴛᴇ ʜᴏ\n\n"
        "ᴊɪꜱ ɢᴄ ᴋᴏ ᴍᴜᴛᴇ ᴋᴀʀɴᴀ ʜ ᴜꜱ ᴍᴇ ʏᴇ ᴄᴍᴅ ᴅᴏ\n"
        ".ᴄʜᴜᴘ ᴀʟʟ\n\n"
        "ᴜɴᴍᴜᴛᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ\n"
        ".ʙᴏʟ ᴀʟʟ"
    )
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"info_cleaning"))
async def info_cleaning_cb(event):
    await event.answer()
    text = fontify(
        "ᴄʟᴇᴀɴɪɴɢ - ɪꜱ ᴄᴍᴅ ꜱᴇ ɢᴄ ᴋɪ ꜱᴀᴀꜰ ꜱᴀꜰᴀɪ ʜᴏᴛɪ ʜ\n\n"
        ".ᴄʟᴇᴀɴɪɴɢ ᴏɴ - ɪꜱ ꜱᴇ ɢᴄ ᴍᴇ ꜱᴀꜰᴀɪ ꜱᴛᴀʀᴛ ʜᴏɢɪ\n\n"
        ".ᴄʟᴇᴀɴɪɴɢ ᴏꜰꜰ - ɪꜱ ꜱᴇ ꜱᴀꜰᴀɪ ʀᴜᴋ ᴊᴀʏᴇɢɪ"
    )
    buttons = [[Button.inline("「 ʙᴀᴄᴋ 」", b"pro_cmds_menu")]]
    await safe_edit_card(event, text, buttons, collapsed=True)

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
    await safe_edit_card(event, HEAVY_ANIMATIONS_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_gauges"))
async def fun_cat_gauges_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, FUN_GAUGES_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_games"))
async def fun_cat_games_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, GAMES_TOOLS_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_core"))
async def fun_cat_core_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, CORE_TOOLS_TEXT, buttons, collapsed=True)

@bot.on(events.CallbackQuery(data=b"fun_cat_random"))
async def fun_cat_random_cb(event):
    await event.answer()
    buttons = [[Button.inline("↺ ʙᴀᴄᴋ ↻", b"fun_cmds_menu")]]
    await safe_edit_card(event, RANDOM_SECTION_TEXT, buttons, collapsed=True)

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
#             BULLETPROOF BROADCAST ENGINE (OWNER ONLY)
# ============================================================

@bot.on(events.NewMessage(pattern=r"^/broadcast(?: (.+))?"))
async def broadcast_handler(event):
    if event.sender_id != OWNER_ID:
        return

    reply = await event.get_reply_message()
    custom_text = event.pattern_match.group(1)
    if not reply and not custom_text:
        await event.respond("⚠️ ᴋɪꜱɪ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `/broadcast` ʟɪᴋʜᴏ ʏᴀ `/broadcast <text>` ʙʜᴇᴊᴏ.")
        return

    status = await event.respond("🔍 **ᴛᴀʀɢᴇᴛꜱ ɢᴀᴛʜᴇʀ ʜᴏ ʀᴀʜᴇ ʜᴀɪɴ...**")

    target_ids = set()

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

    try:
        async for dialog in bot.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                target_ids.add(dialog.id)
    except Exception as e:
        print(f"[Dialogs Fetch Error]: {e}")

    total = len(target_ids)
    if total == 0:
        await status.edit("❌ **ᴅᴀᴛᴀʙᴀꜱᴇ ᴍᴇ ᴋᴏɪ ʙʜɪ ᴜꜱᴇʀꜱ ʏᴀ ɢʀᴏᴜᴩꜱ ɴᴀʜɪ ᴍɪʟᴇ ʙʀᴏᴀᴅᴄᴀꜱᴛ ᴋᴇ ʟɪʏᴇ!**")
        return

    await status.edit(f"🚀 **ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜱᴛᴀʀᴛᴇᴅ!**\nᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛꜱ: `{total}`\nᴩʀᴏɢʀᴇꜱꜱ: `0/{total}`")

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
        except Exception as e:
            failed += 1
            print(f"[Broadcast Error on {target}]: {e}")

        if idx % 15 == 0:
            try:
                await status.edit(f"⏳ **ʙʀᴏᴀᴅᴄᴀꜱᴛɪɴɢ...**\nᴅᴏɴᴇ: `{idx}/{total}`\nꜱᴜᴄᴄᴇꜱꜱ: `{success}`\nꜰᴀɪʟᴇᴅ: `{failed}`")
            except Exception:
                pass

    await status.edit(
        f"✅ **ʙʀᴏᴀᴅᴄᴀꜱᴛ ꜰɪɴɪꜱʜᴇᴅ!**\n\n"
        f"🎯 ᴅᴇʟɪᴠᴇʀᴇᴅ: `{success}`\n"
        f"❌ ꜰᴀɪʟᴇᴅ / ʙʟᴏᴄᴋᴇᴅ: `{failed}`\n"
        f"📊 ᴛᴏᴛᴀʟ ᴛᴀʀɢᴇᴛꜱ: `{total}`"
    )

# ============================================================
#             USERBOT COMMANDS (ATTACHED PER CLIENT)
# ============================================================

def register_userbot_handlers(uclient: TelegramClient, owner_uid: int):

    if owner_uid not in active_raids:
        active_raids[owner_uid] = set()
    if owner_uid not in active_reply_raids:
        active_reply_raids[owner_uid] = set()

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

        await uclient.send_message(
            "me",
            f"🚀 **ᴏɴᴇ ᴡᴏʀᴅ 2.0 ꜱᴛᴀʀᴛᴇᴅ!**\nᴛᴀʀɢᴇᴛ ɪᴅ: `{target_user_id}`\nʀᴇᴍᴀɪɴɪɴɢ ᴡᴏʀᴅꜱ: `{len(words)}`\nꜱᴩᴇᴇᴅ: `0.3s`"
        )

        while words and auto_raid_active.get(owner_uid, False):
            word = words[0]
            try:
                latest_msgs = await uclient.get_messages(entity, from_user=target_user_id, limit=1)

                if not latest_msgs or isinstance(latest_msgs[0], MessageEmpty):
                    auto_raid_active[owner_uid] = False
                    await uclient.send_message(
                        "me",
                        "🛑 **ᴛᴀʀɢᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ᴅᴇʟᴇᴛᴇ ʜᴏ ɢᴀʏᴀ ʜᴀɪ! ʀᴀɪᴅ ꜱᴛᴏᴩᴩᴇᴅ.**\n\nɴᴀʏᴀ ᴍᴇꜱꜱᴀɢᴇ ᴀᴀɴᴇ ᴩᴀʀ `.restart` ʙʜᴇᴊ ᴋᴀʀ ʙᴀᴀᴋɪ ᴡᴏʀᴅꜱ ʀᴇꜱᴜᴍᴇ ᴋᴀʀᴇɪɴ."
                    )
                    break

                target_latest_id = latest_msgs[0].id

                await uclient.send_message(
                    entity,
                    word,
                    reply_to=target_latest_id
                )

                words.pop(0)
                await asyncio.sleep(0.3)

            except FloodWaitError as fwe:
                await uclient.send_message("me", f"⚠️ ʀᴀᴛᴇ ʟɪᴍɪᴛᴇᴅ! ᴩᴀᴜꜱɪɴɢ ꜰᴏʀ `{fwe.seconds}` ꜱᴇᴄᴏɴᴅꜱ...")
                await asyncio.sleep(fwe.seconds + 1)
            except RPCError as rpc_err:
                auto_raid_active[owner_uid] = False
                await uclient.send_message("me", f"❌ ᴛᴇʟᴇɢʀᴀᴍ ᴀᴩɪ ᴇʀʀᴏʀ: `{rpc_err}`")
                break
            except Exception as e:
                auto_raid_active[owner_uid] = False
                await uclient.send_message("me", f"❌ ᴜɴᴇxᴩᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ: `{e}`")
                break

        auto_raid_active[owner_uid] = False

        if not words:
            if owner_uid in auto_user_states:
                auto_user_states[owner_uid].pop(sender_id, None)
            await uclient.send_message("me", "🏁 **ᴏɴᴇ ᴡᴏʀᴅ 2.0 ᴄᴏᴍᴩʟᴇᴛᴇ! ꜱᴀᴀʀᴇ ᴡᴏʀᴅꜱ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʙʜᴇᴊ ᴅɪʏᴇ ɢᴀʏᴇ.**")

    async def timebio_loop():
        ist = timezone(timedelta(hours=5, minutes=30))
        while True:
            try:
                now_str = datetime.now(ist).strftime("%I:%M %p")
                bio_text = f"𝚨 𝐒 𝚮 𝚰 𝐒 𝚮 | 🕒 {now_str} IST | Powered by Hoster"
                await uclient(UpdateProfileRequest(about=bio_text))
            except Exception as e:
                print(f"[TimeBio Error]: {e}")
            await asyncio.sleep(60)

    # ========== LOGOUT & HELP ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.logout$"))
    async def uclient_logout(event):
        active_raids[owner_uid].discard(event.chat_id)
        auto_raid_active[owner_uid] = False
        await reply_card(uclient, event, "🚪 **ᴜꜱᴇʀʙᴏᴛ ᴅɪꜱᴄᴏɴɴᴇᴄᴛᴇᴅ & ꜱᴇꜱꜱɪᴏɴ ʀᴇᴍᴏᴠᴇᴅ ꜰʀᴏᴍ ꜱᴇʀᴠᴇʀ.**", collapsed=False)
        await perform_logout(owner_uid)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.help$"))
    async def help_cmd(event):
        await reply_card(uclient, event, HELP_TEXT, collapsed=True)

    # ========== TIMEBIO & PURGE & TTS & AFK ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.timebio\s+(on|off)$"))
    async def timebio_cmd(event):
        mode = event.pattern_match.group(1).lower()
        if mode == "on":
            if owner_uid in user_timebio_tasks and not user_timebio_tasks[owner_uid].done():
                await reply_card(uclient, event, "⚠️ ᴛɪᴍᴇʙɪᴏ ᴩᴇʜʟᴇ ꜱᴇ ʜɪ ʀᴜɴɴɪɴɢ ʜᴀɪ!", collapsed=False)
                return
            user_timebio_tasks[owner_uid] = asyncio.create_task(timebio_loop())
            await reply_card(uclient, event, "✅ **ᴛɪᴍᴇʙɪᴏ ᴇɴᴀʙʟᴇᴅ!** ᴩʀᴏꜰɪʟᴇ ʙɪᴏ ʜᴀʀ ᴍɪɴᴜᴛᴇ ɪɴᴅɪᴀɴ ꜱᴛᴀɴᴅᴀʀᴅ ᴛɪᴍᴇ ꜱᴇ ʟɪᴠᴇ ᴜᴩᴅᴀᴛᴇ ʜᴏɢᴀ.", collapsed=False)
        else:
            task = user_timebio_tasks.pop(owner_uid, None)
            if task:
                task.cancel()
            await reply_card(uclient, event, "🛑 **ᴛɪᴍᴇʙɪᴏ ᴅɪꜱᴀʙʟᴇᴅ!**", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.purge(?:\s+(\d+))?$"))
    async def purge_cmd(event):
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

        noti = await send_card(uclient, chat_id, "🧹 **ᴩᴜʀɢᴇ ᴄᴏᴍᴩʟᴇᴛᴇ! ᴍᴇꜱꜱᴀɢᴇꜱ ᴄʟᴇᴀɴᴇᴅ.**", collapsed=False)
        await asyncio.sleep(2)
        try:
            await noti.delete()
        except Exception:
            pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.tts(?:\s+(.+))?"))
    async def tts_cmd(event):
        text = event.pattern_match.group(1)
        if not text:
            reply = await event.get_reply_message()
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
            await uclient.send_file(event.chat_id, file_name, voice_note=True)
        except Exception as e:
            await send_card(uclient, event.chat_id, f"❌ TTS Error: `{e}`", collapsed=False)
        finally:
            if os.path.exists(file_name):
                os.remove(file_name)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.afk(?:\s+(.+))?$"))
    async def afk_on(event):
        reason = event.pattern_match.group(1) or "Busy"
        user_afk_data[owner_uid] = {
            "status": True,
            "reason": reason,
            "start": time.monotonic(),
            "pings": []
        }
        await reply_card(uclient, event, f"💤 **ᴀꜰᴋ ᴍᴏᴅᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!**\nReason: `{reason}`", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True))
    async def afk_off_check(event):
        if owner_uid in user_afk_data and user_afk_data[owner_uid]["status"]:
            if event.raw_text.startswith(".afk"):
                return
            data = user_afk_data.pop(owner_uid)
            dur = int(time.monotonic() - data["start"])
            m, s = divmod(dur, 60)
            h, m = divmod(m, 60)
            seen_time = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"
            
            pings_count = len(data["pings"])
            await reply_card(uclient, event, f"☀️ **ᴡᴇʟᴄᴏᴍᴇ ʙᴀᴄᴋ! ᴀꜰᴋ ᴍᴏᴅᴇ ᴅɪꜱᴀʙʟᴇᴅ.**\nᴀᴀᴩ `{seen_time}` ᴛᴀᴋ ᴏꜰꜰʟɪɴᴇ ᴛʜᴇ. ᴍᴇɴᴛɪᴏɴꜱ: `{pings_count}`", collapsed=False)

    @uclient.on(events.NewMessage(incoming=True))
    async def afk_listener(event):
        if owner_uid not in user_afk_data or not user_afk_data[owner_uid]["status"]:
            return

        should_reply = False
        if event.is_private and not event.sender_id == owner_uid:
            should_reply = True
        elif event.mentioned:
            should_reply = True

        if should_reply:
            data = user_afk_data[owner_uid]
            dur = int(time.monotonic() - data["start"])
            m, s = divmod(dur, 60)
            h, m = divmod(m, 60)
            seen_time = f"{h}h {m}m {s}s" if h else f"{m}m {s}s"

            sender = await event.get_sender()
            sname = sender.first_name if sender else "User"
            data["pings"].append((event.sender_id, sname))

            msg_box = (
                f"👋 **ᴍᴀꜱᴛᴇʀ ᴀʙʜɪ ᴀꜰᴋ ʜᴀɪɴ!**\n\n"
                f"📌 Reason: `{data['reason']}`\n"
                f"⏱ Offline Since: `{seen_time}`"
            )
            try:
                await event.reply(msg_box)
            except Exception:
                pass

    # ========== RAID / SPAM / ONE-WORD / REPLY RAID ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.reboot$"))
    async def reboot_cmd(event):
        active_raids[owner_uid].discard(event.chat_id)
        active_reply_raids[owner_uid].clear()
        auto_raid_active[owner_uid] = False
        try:
            await event.delete()
        except Exception:
            pass
        msg = await send_card(
            uclient,
            event.chat_id,
            "🔄 **ᴀʟʟ ᴀᴄᴛɪᴠᴇ ʀᴀɪᴅꜱ, ꜱᴩᴀᴍ & ʀᴇᴩʟʏ-ʀᴀɪᴅꜱ ᴛᴇʀᴍɪɴᴀᴛᴇᴅ! ᴜꜱᴇʀʙᴏᴛ ʀᴇꜰʀᴇꜱʜᴇᴅ!**",
            collapsed=False
        )
        await asyncio.sleep(1.5)
        try:
            await msg.delete()
        except Exception:
            pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rraid$"))
    async def rraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.rraid` ʟɪᴋʜᴏ.", collapsed=False)
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **ᴏᴡɴᴇʀ ᴩᴀʀ ʀᴇᴩʟʏ ʀᴀɪᴅ ʟᴀɢᴀɴᴀ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
            return

        active_reply_raids[owner_uid].add(reply.sender_id)
        await reply_card(uclient, event, f"⚔️ **ʀᴇᴩʟʏ ʀᴀɪᴅ ᴀᴄᴛɪᴠᴀᴛᴇᴅ ᴏɴ:** `{reply.sender_id}`\n\n_Type `.drraid` or `.reboot` to stop._", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.drraid$"))
    async def drraid_cmd(event):
        reply = await event.get_reply_message()
        if reply and reply.sender_id in active_reply_raids[owner_uid]:
            active_reply_raids[owner_uid].discard(reply.sender_id)
            await reply_card(uclient, event, f"🛑 **ʀᴇᴩʟʏ ʀᴀɪᴅ ꜱᴛᴏᴩᴩᴇᴅ ꜰᴏʀ:** `{reply.sender_id}`", collapsed=False)
        else:
            active_reply_raids[owner_uid].clear()
            await reply_card(uclient, event, "🛑 **ᴀʟʟ ᴀᴄᴛɪᴠᴇ ʀᴇᴩʟʏ ʀᴀɪᴅꜱ ꜱᴛᴏᴩᴩᴇᴅ!**", collapsed=False)

    @uclient.on(events.NewMessage(incoming=True))
    async def reply_raid_listener(event):
        if event.sender_id in active_reply_raids.get(owner_uid, set()):
            try:
                await event.reply(random.choice(RAID_TEXTS))
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds)
            except Exception:
                pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.raid(?: (.+))?"))
    async def raid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.raid [count]` ʟᴀɢᴀᴏ.", collapsed=False)
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **ᴏᴡɴᴇʀ ɪᴅ ᴩᴀʀ ʀᴀɪᴅ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
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
                await uclient.send_message(
                    chat_id,
                    random.choice(RAID_TEXTS),
                    reply_to=reply.id
                )
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break

        active_raids[owner_uid].discard(chat_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.mraid(?: (.+))?"))
    async def mraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.mraid [count]` ʟᴀɢᴀᴏ.", collapsed=False)
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **ᴏᴡɴᴇʀ ɪᴅ ᴩᴀʀ ʀᴀɪᴅ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
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
                await uclient.send_message(
                    chat_id,
                    f"{mention_str}{random.choice(RAID_TEXTS)}",
                    reply_to=reply.id
                )
                await asyncio.sleep(0.35)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break

        active_raids[owner_uid].discard(chat_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sraid(?: (.+))?"))
    async def sraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.sraid` ʟᴀɢᴀᴏ.", collapsed=False)
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **ᴏᴡɴᴇʀ ɪᴅ ᴩᴀʀ ʀᴀɪᴅ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
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
                await uclient.send_message(
                    chat_id,
                    random.choice(RAID_TEXTS),
                    reply_to=reply.id
                )
                await asyncio.sleep(0.1) # 10 msg/sec
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break

        active_raids[owner_uid].discard(chat_id)

    # .oneraid (Original 1.0)
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.oneraid(?: (.+))?"))
    async def oneraid_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴛᴀʀɢᴇᴛ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.oneraid [count/text]` ʟᴀɢᴀᴏ.", collapsed=False)
            return

        if reply.sender_id == OWNER_ID:
            await reply_card(uclient, event, "🛡️ **ᴏᴡɴᴇʀ ɪᴅ ᴩᴀʀ ʀᴀɪᴅ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
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
                await uclient.send_message(
                    chat_id,
                    word,
                    reply_to=reply.id
                )
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break

        active_raids[owner_uid].discard(chat_id)

    # ========== ONE WORD 2.0 (SMART LINK ATTACK) ==========

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.auto$"))
    async def start_auto(event):
        if owner_uid not in auto_user_states:
            auto_user_states[owner_uid] = {}
        auto_user_states[owner_uid][event.sender_id] = {"step": "WAITING_LINK"}
        await reply_card(uclient, event, "📍 **[ONE WORD 2.0]** ᴛᴀʀɢᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ʟɪɴᴋ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ ʙʜᴇᴊᴏ.", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.stop$"))
    async def stop_auto(event):
        auto_raid_active[owner_uid] = False
        await reply_card(uclient, event, "🛑 **[ONE WORD 2.0]** ʀᴀɪᴅ ꜱᴛᴏᴩᴩᴇᴅ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ.", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.restart$"))
    async def restart_auto(event):
        sender_id = event.sender_id
        state = auto_user_states.get(owner_uid, {}).get(sender_id)

        if not state or not state.get("remaining_words"):
            await reply_card(uclient, event, "❌ ʀᴇꜱᴜᴍᴇ ᴋᴀʀɴᴇ ᴋᴇ ʟɪʏᴇ ᴋᴏɪ ᴩᴇɴᴅɪɴɢ ꜱᴇꜱꜱɪᴏɴ ɴᴀʜɪ ᴍɪʟᴀ! ɴᴀʏᴇ ꜱɪʀᴇ ꜱᴇ `.auto` ᴜꜱᴇ ᴋᴀʀᴇɪɴ.", collapsed=False)
            return

        if auto_raid_active.get(owner_uid, False):
            await reply_card(uclient, event, "⚠️ ᴏɴᴇ ᴡᴏʀᴅ 2.0 ᴩᴇʜʟᴇ ꜱᴇ ᴀᴄᴛɪᴠᴇ ʜᴀɪ!", collapsed=False)
            return

        await run_smart_auto_raid(sender_id)

    @uclient.on(events.NewMessage(outgoing=True))
    async def auto_workflow_handler(event):
        sender_id = event.sender_id
        if owner_uid not in auto_user_states or sender_id not in auto_user_states[owner_uid]:
            return

        current_state = auto_user_states[owner_uid][sender_id]

        if current_state.get("step") == "WAITING_LINK" and event.is_reply:
            link = event.raw_text.strip()
            chat_identifier, msg_id = parse_telegram_link(link)

            if not chat_identifier or not msg_id:
                await reply_card(uclient, event, "❌ ɪɴᴠᴀʟɪᴅ ʟɪɴᴋ ꜰᴏʀᴍᴀᴛ! ᴅɪʀᴇᴄᴛ ᴍᴇꜱꜱᴀɢᴇ ʟɪɴᴋ ʀᴇᴩʟʏ ᴋᴀʀᴏ.", collapsed=False)
                return

            try:
                entity = await uclient.get_entity(chat_identifier)
                target_msg = await uclient.get_messages(entity, ids=msg_id)

                if not target_msg or isinstance(target_msg, MessageEmpty) or not target_msg.sender_id:
                    auto_user_states[owner_uid].pop(sender_id, None)
                    await reply_card(uclient, event, "❌ ᴛᴀʀɢᴇᴛ ᴍᴇꜱꜱᴀɢᴇ ᴍɪꜱꜱɪɴɢ ᴏʀ ᴅᴇʟᴇᴛᴇᴅ!", collapsed=False)
                    return

                current_state["entity"] = entity
                current_state["target_user_id"] = target_msg.sender_id
                current_state["step"] = "WAITING_TEXT"

                await reply_card(uclient, event, "✅ ᴛᴀʀɢᴇᴛ ɪᴅᴇɴᴛɪꜰɪᴇᴅ! ᴀʙ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ ᴡᴏ **ᴛᴇxᴛ/ᴡᴏʀᴅꜱ** ʙʜᴇᴊᴏ ᴊᴏ ᴀᴛᴛᴀᴄᴋ ᴍᴇ ʙʜᴇᴊɴᴇ ʜᴀɪɴ.", collapsed=False)

            except Exception as e:
                auto_user_states[owner_uid].pop(sender_id, None)
                await reply_card(uclient, event, f"⚠️ Resolution Error: `{e}`", collapsed=False)

        elif current_state.get("step") == "WAITING_TEXT" and event.is_reply:
            raw_text = event.raw_text.strip()
            words = raw_text.split()

            current_state["remaining_words"] = words
            current_state["step"] = "RUNNING"

            await run_smart_auto_raid(sender_id)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.spam(?: (.+))?"))
    async def spam_cmd(event):
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
        if reply and reply.sender_id == OWNER_ID:
            await send_card(uclient, chat_id, "🛡️ **ᴏᴡɴᴇʀ ɪᴅ ᴩᴀʀ ꜱᴩᴀᴍ ᴩʀᴏʜɪʙɪᴛᴇᴅ ʜᴀɪ!**", collapsed=False)
            active_raids[owner_uid].discard(chat_id)
            return

        reply_to_id = reply.id if (reply and reply.sender_id) else None

        for _ in range(count):
            if chat_id not in active_raids[owner_uid]:
                break
            try:
                await uclient.send_message(
                    chat_id,
                    text,
                    reply_to=reply_to_id
                )
                await asyncio.sleep(0.3)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                break

        active_raids[owner_uid].discard(chat_id)

    # ========== ANIMATION: .type / .typ (NATURAL HUMAN TYPING SPEED) ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.(?:type|typ)(?: (.+))?"))
    async def type_cmd(event):
        text = event.pattern_match.group(1)
        if not text:
            reply = await event.get_reply_message()
            if reply and (reply.text or reply.message):
                text = reply.text or reply.message
            else:
                await reply_card(uclient, event, "⚠️ Usage: `.type Aapka Text Yahan`", collapsed=False)
                return

        styled_text = fontify(text)
        typing_symbol = "▒"
        accumulated = ""

        # Natural human speed (approx 0.18s per char)
        for char in styled_text:
            accumulated += char
            try:
                await event.edit(f"{accumulated}{typing_symbol}")
                await asyncio.sleep(0.18)
            except FloodWaitError as e:
                await asyncio.sleep(e.seconds + 1)
            except Exception:
                pass

        try:
            await event.edit(accumulated)
        except Exception:
            pass

    # ========== ANIMATION: .fuck (RAW ANIMATION FRAMES, FAST LIKE BEFORE) ==========
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fuck$"))
    async def fuck_anim_cmd(event):
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

        msg = await uclient.send_message(event.chat_id, frames[0], link_preview=False)
        for f in frames[1:]:
            await asyncio.sleep(0.35)  # Fast original animation speed
            try:
                await msg.edit(f, link_preview=False)
            except Exception:
                pass

    # ----------------- CLONE & RESTORE ENGINE -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.clone$"))
    async def clone_cmd(event):
        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            await reply_card(uclient, event, "⚠️ ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴋᴏ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.clone` ʀᴜɴ ᴋᴀʀᴏ.", collapsed=False)
            return

        try:
            await event.delete()
        except Exception:
            pass

        msg = await send_card(uclient, event.chat_id, "🔄 **ᴄʟᴏɴɪɴɢ ᴛᴀʀɢᴇᴛ ᴩʀᴏꜰɪʟᴇ ɪᴅᴇɴᴛɪᴛʏ...**", collapsed=False)

        try:
            target_user = await uclient.get_entity(reply.sender_id)
        except Exception as e:
            await edit_card(msg, f"❌ Failed to fetch user: `{e}`", collapsed=False)
            return

        if target_user.id == OWNER_ID and owner_uid != OWNER_ID:
            await edit_card(msg, "🛡️ **ᴏᴡɴᴇʀ ᴀᴄᴄᴏᴜɴᴛ ᴋᴏ ᴄʟᴏɴᴇ ᴋᴀʀɴᴀ ᴀʟʟᴏᴡᴇᴅ ɴᴀʜɪ ʜᴀɪ!**", collapsed=False)
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

            await edit_card(msg, f"✅ **ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ᴄʟᴏɴᴇᴅ {target_first}!**\n\n_Type `.back` to restore original profile._", collapsed=False)
        except AboutTooLongError:
            await edit_card(msg, "⚠️ ᴛᴀʀɢᴇᴛ ʙɪᴏ ɪꜱ ᴛᴏᴏ ʟᴏɴɢ, ᴄʟᴏɴᴇᴅ ɴᴀᴍᴇ ᴏɴʟʏ.", collapsed=False)
        except Exception as e:
            await edit_card(msg, f"❌ Clone Error: `{e}`", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.back$"))
    async def back_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass

        if owner_uid not in backup_profiles:
            await send_card(uclient, event.chat_id, "⚠️ ᴋᴏɪ ᴩʀᴏꜰɪʟᴇ ʙᴀᴄᴋᴜᴩ ɴᴀʜɪ ᴍɪʟᴀ ʏᴀ ᴀᴀᴩ ᴩᴇʜʟᴇ ꜱᴇ ᴏʀɪɢɪɴᴀʟ ꜱᴛᴀᴛᴇ ᴍᴇ ʜᴀɪɴ.", collapsed=False)
            return

        msg = await send_card(uclient, event.chat_id, "🔄 **ʀᴇꜱᴛᴏʀɪɴɢ ᴏʀɪɢɪɴᴀʟ ᴩʀᴏꜰɪʟᴇ...**", collapsed=False)
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
            await edit_card(msg, "✅ **ᴩʀᴏꜰɪʟᴇ ꜱᴜᴄᴄᴇꜱꜱꜰᴜʟʟʏ ʀᴇꜱᴛᴏʀᴇᴅ ᴛᴏ ᴏʀɪɢɪɴᴀʟ ɪᴅᴇɴᴛɪᴛʏ!**", collapsed=False)
        except Exception as e:
            await edit_card(msg, f"❌ Restore Error: `{e}`", collapsed=False)

    # ----------------- SILENT TOOLS -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chup(?:\s+(all))?$"))
    async def chup_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass

        arg = event.pattern_match.group(1)
        chat_id = event.chat_id

        if arg and arg.lower() == "all":
            u_chup_all[owner_uid].add(chat_id)
            try:
                await uclient.send_message("me", f"🔇 **ꜱɪʟᴇɴᴛ ᴍᴜᴛᴇ ᴀᴄᴛɪᴠᴀᴛᴇᴅ!**\nChat ID: `{chat_id}`\nMode: ALL incoming messages auto-delete.")
            except Exception:
                pass
            return

        reply = await event.get_reply_message()
        if not reply or not reply.sender_id:
            try:
                await uclient.send_message("me", "⚠️ **ᴄʜᴜᴩ ᴄᴏᴍᴍᴀɴᴅ ꜰᴀɪʟᴇᴅ:** ᴋɪꜱɪ ᴜꜱᴇʀ ᴋᴇ ᴍᴇꜱꜱᴀɢᴇ ᴩᴀʀ ʀᴇᴩʟʏ ᴋᴀʀᴋᴇ `.chup` ʟᴀɢᴀᴏ ʏᴀ `.chup all` ᴜꜱᴇ ᴋᴀʀᴏ.")
            except Exception:
                pass
            return

        target_id = reply.sender_id
        if target_id == owner_uid:
            return

        if chat_id not in u_chup_targets[owner_uid]:
            u_chup_targets[owner_uid][chat_id] = set()
        u_chup_targets[owner_uid][chat_id].add(target_id)

        try:
            await uclient.send_message("me", f"🤐 **ᴛᴀʀɢᴇᴛ ꜱɪʟᴇɴᴄᴇᴅ ꜱɪʟᴇɴᴛʟʏ!**\nTarget ID: `{target_id}`\nChat ID: `{chat_id}`")
        except Exception:
            pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bol(?:\s+(all))?$"))
    async def bol_cmd(event):
        try:
            await event.delete()
        except Exception:
            pass

        arg = event.pattern_match.group(1)
        chat_id = event.chat_id

        if arg and arg.lower() == "all":
            u_chup_all[owner_uid].discard(chat_id)
            try:
                await uclient.send_message("me", f"🔊 **ɢʀᴏᴜᴩ ᴜɴᴍᴜᴛᴇᴅ!**\nChat ID: `{chat_id}`\nMode: Sabhi normal baat kar sakte hain.")
            except Exception:
                pass
            return

        reply = await event.get_reply_message()
        if reply and reply.sender_id:
            target_id = reply.sender_id
            if chat_id in u_chup_targets[owner_uid]:
                u_chup_targets[owner_uid][chat_id].discard(target_id)
            try:
                await uclient.send_message("me", f"🗣️ **ᴛᴀʀɢᴇᴛ ᴜɴ-ꜱɪʟᴇɴᴄᴇᴅ!**\nTarget ID: `{target_id}`\nChat ID: `{chat_id}`")
            except Exception:
                pass
        else:
            if chat_id in u_chup_targets[owner_uid]:
                u_chup_targets[owner_uid][chat_id].clear()
            u_chup_all[owner_uid].discard(chat_id)
            try:
                await uclient.send_message("me", f"🔊 **ᴄʜᴀᴛ ʀᴇꜱᴛʀɪᴄᴛɪᴏɴꜱ ᴄʟᴇᴀʀᴇᴅ!**\nChat ID: `{chat_id}`")
            except Exception:
                pass

    @uclient.on(events.NewMessage(incoming=True))
    async def incoming_cleaner_and_silencer(event):
        chat_id = event.chat_id

        if chat_id in u_cleaning_chats.get(owner_uid, set()):
            try:
                await event.delete()
            except Exception:
                pass
            return

        if chat_id in u_chup_all.get(owner_uid, set()):
            if event.sender_id != owner_uid and event.sender_id != OWNER_ID:
                try:
                    await event.delete()
                except Exception:
                    pass
            return

        targets = u_chup_targets.get(owner_uid, {}).get(chat_id, set())
        if event.sender_id in targets:
            try:
                await event.delete()
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
        except Exception:
            pass

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.cleaning\s+(on|off)$"))
    async def cleaning_cmd(event):
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
                await uclient.send_message("me", f"🧹 **ᴄʟᴇᴀɴɪɴɢ ꜱᴛᴀʀᴛᴇᴅ ꜱɪʟᴇɴᴛʟʏ!**\nChat ID: `{chat_id}`\nMode: Deleting all chat messages.")
            except Exception:
                pass
        else:
            u_cleaning_chats[owner_uid].discard(chat_id)
            try:
                await uclient.send_message("me", f"🛑 **ᴄʟᴇᴀɴɪɴɢ ꜱᴛᴏᴩᴩᴇᴅ!**\nChat ID: `{chat_id}`")
            except Exception:
                pass

    # ----------------- LIVE ANIMATIONS (FAST ORIGINAL SPEED) -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.gadi$"))
    async def gadi_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Door se loud horn ki aawaz aa rahi hai... 🔊",
            "Kaali Thar drift maarte hue aayi! 🚙💨",
            "💨💨💨 (Dhool udd gayi poori chat me)",
            "🕶️ Utar gaya Bhai! System hang ho chuka hai chat ka! 👑",
        ]
        msg = await send_card(uclient, event.chat_id, f"🚙 **SYSTEM ENTRY**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🚙 **SYSTEM ENTRY**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.moye$"))
    async def moye_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Aapki baatein suni ja rahi hain... 🧐",
            "Analyzing life choices... 📉",
            "Emotional damage detected: 100% 💔",
            "🎶 *Moye Moye... Moye Moye...* 😭🥀",
        ]
        msg = await send_card(uclient, event.chat_id, f"🥀 **MOYE MOYE**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🥀 **MOYE MOYE**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fbi$"))
    async def fbi_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "🚨 RED ALERT IN THIS CHAT! 🚨",
            "🚁 Helicopters hovering above...",
            "FBI AGENTS KICKING THE DOOR! 🚪💥",
            "🔫👮‍♂️ \"HANDS IN THE AIR! CRINGE POSTING BAN HAI!\" 🚔",
        ]
        msg = await send_card(uclient, event.chat_id, f"🚨 **FBI OPEN UP**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🚨 **FBI OPEN UP**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.thanos$"))
    async def thanos_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Target pe nazar gadhayi ja rahi hai... 👁️",
            "Infinity Gauntlet ready... 🧤✨",
            "*SNAP!* 🫰",
            "Target dhool ban ke hawa me udd gaya! 💨💀",
        ]
        msg = await send_card(uclient, event.chat_id, f"🧤 **THANOS SNAP**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🧤 **THANOS SNAP**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.burn$"))
    async def burn_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Jalne ki badboo aa rahi hai chat me... 👃",
            "Emergency medical kit dispatched... 🚑💨",
            "📦 Burnol delivered safely to target! Thanda laga lo bhai 😂",
        ]
        msg = await send_card(uclient, event.chat_id, f"🔥 **BURNOL EXPRESS**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🔥 **BURNOL EXPRESS**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.crying$"))
    async def crying_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "(ಥ_ಥ)",
            "(ಥ﹏ಥ)",
            "(༎ຶ⌑༎ຶ)",
            "🌊 Aansuo ki baadh aa gayi chat me! Kisne rulaya isko? 😭",
        ]
        msg = await send_card(uclient, event.chat_id, f"😭 **EMOTIONAL DAMAGE**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"😭 **EMOTIONAL DAMAGE**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.snitch$"))
    async def snitch_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Chat me spy drone enter ho raha hai... 🛸",
            "Radar scanning secret chats... 🔍",
            "📸 Secret snapshot captured: Ye banda chupke se gossip padh raha hai!",
        ]
        msg = await send_card(uclient, event.chat_id, f"📸 **SPY DRONE**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"📸 **SPY DRONE**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fight$"))
    async def fight_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "(ง •̀_•́)ง Ring me entry...",
            "🥊 DUSH! Left hook...",
            "💥 DISKHOOM! Direct jaw pe...",
            "(x_x) KNOCK OUT in Round 1! 🏆",
        ]
        msg = await send_card(uclient, event.chat_id, f"🥊 **BOXING MATCH**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🥊 **BOXING MATCH**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.thappad$"))
    async def thappad_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Target lock kiya ja raha hai... 🎯",
            "Mummy ki 100km/h flying chappal launch ho gayi! 🩴💨",
            "🩴💨 . . . . 🎯",
            "🩴💨 . . 🎯",
            "💥 CHATAAAAK! Gulaal nikal gaya muh se! 😵‍💫",
        ]
        msg = await send_card(uclient, event.chat_id, f"🩴 **FLYING CHAPPAL**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🩴 **FLYING CHAPPAL**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rip$"))
    async def rip_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Bande ke aakhri shabd sune ja rahe hain... 👂",
            "⚰️ Coffin uthaya ja raha hai...",
            "🕺🕺⚰️🕺🕺 *Astronomia beats playing...*",
            "🪦 Rest In Peace Bhai! Agle janam me thoda dimag leke aana! 💐",
        ]
        msg = await send_card(uclient, event.chat_id, f"⚰️ **SHRADHANJALI**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"⚰️ **SHRADHANJALI**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.binod$"))
    async def binod_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Decrypting mysterious protocol... 💻",
            "Bypassing quantum firewall... 010101",
            "Final secret discovered: 🤫",
            "👑 \"BINOD\" 👑\n\n(Bas yahi kehna tha!) 😂",
        ]
        msg = await send_card(uclient, event.chat_id, f"🤫 **BINOD ENCRYPTION**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🤫 **BINOD ENCRYPTION**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chai$"))
    async def chai_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Stove pe suspense garam ho raha hai... 🔥",
            "Adrak aur elaichi koot ke daali... 🫚",
            "Ubaal aa raha hai... ☕💨",
            "☕ Garam Garam Tapri Chai Ready!\nChuski lo aur bakwaas band karo! 😎",
        ]
        msg = await send_card(uclient, event.chat_id, f"☕ **TAPRI CHAI MAKER**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"☕ **TAPRI CHAI MAKER**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.ghost$"))
    async def ghost_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Chat ki lights flicker ho rahi hain... 💡",
            "💡⬛💡⬛ (Andhera chha gaya)",
            "Peeche koi khada hai... 👤",
            "👻 BHOOOOO! Darr gaya na bacche? 😂",
        ]
        msg = await send_card(uclient, event.chat_id, f"👻 **BHOOT PRANK**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"👻 **BHOOT PRANK**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bomb$"))
    async def bomb_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        msg = await send_card(uclient, event.chat_id, "💣 TICK... 3", collapsed=False, reply_to=reply_to_id)
        await asyncio.sleep(0.4)
        await edit_card(msg, "💣 TICK... 2", collapsed=False)
        await asyncio.sleep(0.4)
        await edit_card(msg, "💣 TICK... 1", collapsed=False)
        await asyncio.sleep(0.4)
        outcomes = [
            "💥 **BOOOOOOM! Chat destroyed!** 💀",
            "✂️ **Green wire cut! Bomb defused safely!** 😌",
            "💨 **Pssss... Fuski bomb nikla!** 😂",
        ]
        await edit_card(msg, random.choice(outcomes), collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.heart$"))
    async def heart_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        colors = ["🖤", "🤎", "💜", "💙", "💚", "💛", "🧡", "❤️‍🔥", "❤️"]
        msg = await send_card(uclient, event.chat_id, colors[0], collapsed=False, reply_to=reply_to_id)
        for c in colors[1:]:
            await asyncio.sleep(0.2)
            await edit_card(msg, c, collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.loading$"))
    async def loading_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        bars = [
            "[■□□□□□□□□□] 10%",
            "[■■■□□□□□□□] 30%",
            "[■■■■■□□□□□] 50%",
            "[■■■■■■■□□□] 70%",
            "[■■■■■■■■■□] 90%",
            "[■■■■■■■■■■] 100% COMPLETE!",
        ]
        msg = await send_card(uclient, event.chat_id, f"⏳ **SYSTEM LOADING**\n\n{bars[0]}", collapsed=False, reply_to=reply_to_id)
        for b in bars[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"⏳ **SYSTEM LOADING**\n\n{b}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.slap$"))
    async def slap_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "( •_•)",
            "( •_•)>⌐■-■",
            "(⌐■_■)ノ",
            "👋💥 (x_x) Direct 440-Volt Slap!",
        ]
        msg = await send_card(uclient, event.chat_id, frames[0], collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f, collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.coffee$"))
    async def coffee_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        steps = [
            "Heating water...",
            "Grinding beans...",
            "Brewing ▰▱▱▱▱",
            "Brewing ▰▰▰▱▱",
            "Brewing ▰▰▰▰▰",
            "☕ Coffee ready! Enjoy 😎",
        ]
        msg = await send_card(uclient, event.chat_id, f"☕ **COFFEE MACHINE**\n\n{steps[0]}", collapsed=False, reply_to=reply_to_id)
        for s in steps[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"☕ **COFFEE MACHINE**\n\n{s}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.launch$"))
    async def launch_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["🚀 3...", "🚀 2...", "🚀 1...", "🔥 IGNITION!", "🌌 IN ORBIT!"]
        msg = await send_card(uclient, event.chat_id, f"🚀 **ROCKET LAUNCH**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🚀 **ROCKET LAUNCH**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.scan$"))
    async def scan_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["Analyzing cache...", "Checking network sockets...", "Verifying database link...", "✅ System Clean & Optimal!"]
        msg = await send_card(uclient, event.chat_id, f"🛡️ **SAFE DIAGNOSTIC**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"🛡️ **SAFE DIAGNOSTIC**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.matrix$"))
    async def matrix_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = ["01000001 01010011", "01001000 01001001", "01010011 01001000", "🟢 MATRIX STABLE"]
        msg = await send_card(uclient, event.chat_id, f"💻 **MATRIX**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.3)
            await edit_card(msg, f"💻 **MATRIX**\n\n{f}", collapsed=False)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.hack$"))
    async def hack_cmd(event):
        reply = await event.get_reply_message()
        reply_to_id = reply.id if reply else None
        try:
            await event.delete()
        except Exception:
            pass
        frames = [
            "Bypassing mainframe proxy...",
            "Decrypting RSA 4096-bit keys...",
            "Overriding local permissions...",
            "Access Granted: Master Level 🔑",
        ]
        msg = await send_card(uclient, event.chat_id, f"💻 **TERMINAL EMULATION**\n\n{frames[0]}", collapsed=False, reply_to=reply_to_id)
        for f in frames[1:]:
            await asyncio.sleep(0.35)
            await edit_card(msg, f"💻 **TERMINAL EMULATION**\n\n{f}", collapsed=False)

    # ----------------- DESI BANTER & GAUGES -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.gyan(?: (.+))?$"))
    async def gyan_cmd(event):
        target = event.pattern_match.group(1) or "Bhai"
        await reply_card(uclient, event, fun_card("🗣️ GYAN METER", f"Target → {target}\nGyan Speed → Formula 1 (100%)\nVerdict → Bina maange advice pelna band kar! 😂"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.acting(?: (.+))?$"))
    async def acting_cmd(event):
        target = event.pattern_match.group(1) or "Actor"
        await reply_card(uclient, event, fun_card("🎭 OVERACTING SCANNER", f"Target → {target}\nScore → 10/10 ⭐\nVerdict → 50 rupaye kaat re iske overacting ke! ✂️💸"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.kismat$"))
    async def kismat_cmd(event):
        p = random.randint(1, 100)
        remark = "Chai me biskoot girne wali kismat hai teri ☕💀" if p < 30 else "Aadha ghanta late hone par bhi kaam ban jata hai 😎" if p > 70 else "Thoda sambhal ke chalo!"
        await reply_card(uclient, event, fun_card("🎲 KISMAT CHECK", f"Kismat Score → {p}%\nVerdict → {remark}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pappu(?: (.+))?$"))
    async def pappu_cmd(event):
        target = event.pattern_match.group(1) or "Innocent"
        await reply_card(uclient, event, fun_card("😇 MASOOMIYAT METER", f"Candidate → {target}\nMasoomiyat → 0%\nVerdict → Shakal se seedha, harkatein 302 wali! 😈"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bhagode$"))
    async def bhagode_cmd(event):
        await reply_card(uclient, event, fun_card("🏃💨 LURKER DETECTOR", "Status → Seen Zone Champion!\nChat me bas kalesh aur drama dekhne aata hai, bolta kuch nahi 🍿"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.system(?: (.+))?$"))
    async def system_cmd(event):
        target = event.pattern_match.group(1) or "Syshtumm Boy"
        await reply_card(uclient, event, fun_card("🚨 SYSTEM HANG SCORE", f"Target → {target}\nCapacity → ₹5 wala churan\nVerdict → Pehle recharge karwa le, system baad me hilana! 😂"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.chugli(?: (.+))?$"))
    async def chugli_cmd(event):
        target = event.pattern_match.group(1) or "Snake"
        p = random.randint(70, 100)
        await reply_card(uclient, event, fun_card("🐍 CHUGLI RADAR", f"Suspect → {target}\nChugli Level → {p}%\nReport → Abhi dusre group me tumhari hi chugli karke aaya hai! 📡"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fake(?: (.+))?$"))
    async def fake_cmd(event):
        target = event.pattern_match.group(1) or "Showoff"
        await reply_card(uclient, event, fun_card("💸 FAKE RAEES SCAN", f"Target → {target}\nStatus → 100% Fake\nBreakdown → iPhone EMI pe, jacket Sarojini se, attitude Ambani se upar! 🕶️"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bewakoof(?: (.+))?$"))
    async def bewakoof_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        await reply_card(uclient, event, fun_card("🧠 BRAIN CAPACITY SCAN", f"Candidate → {target}\nMemory → 0 KB / 1 TB Free\nVerdict → Sar me dimag nahi, khali ground hai jaha hawa ghoomti hai! 🌪️"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bhaukaal(?: (.+))?$"))
    async def bhaukaal_cmd(event):
        target = event.pattern_match.group(1) or "Don"
        p = random.randint(1, 15)
        await reply_card(uclient, event, fun_card("🦁 BHAUKAAL METER", f"Don → {target}\nBhaukaal → {p}%\nVerdict → Gali ke kutte se darta hai aur chat me badmashi dikha raha hai 🐕💀"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bill$"))
    async def bill_cmd(event):
        amt = random.randint(2500, 9500)
        await reply_card(uclient, event, fun_card("🧾 RESTAURANT BILL PRANK", f"Table No. 4 Final Bill → ₹{amt}\nVerdict → Inke paas wallet bhoolne ka bahana ready hai, pakdo isko! 🏃‍♂️🍽️"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.kutai(?: (.+))?$"))
    async def kutai_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        await reply_card(uclient, event, fun_card("🥊 DIGITAL DHULAI MACHINE", f"Target Lock → {target}\nStatus → Band kamre me digital chappal service start ho gayi hai! 💥🚪"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.shayari$"))
    async def shayari_cmd(event):
        shayaris = [
            "Humne unse pucha kitna chahte ho hume,\nUnhone bola jitna chole me bhatura hota hai! 🍽️",
            "Aasman me udta teer tune pakad liya,\nBina baat ke panga leke apna time barbaad kar diya! 😂",
            "Tere husn ke charche gali gali me the,\nPar jab tu samne aayi to hum andhe hi bhale the! 💀",
        ]
        await reply_card(uclient, event, fun_card("📜 DESI SHAYARI", random.choice(shayaris)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.insult(?: (.+))?$"))
    async def insult_cmd(event):
        target = event.pattern_match.group(1) or "Bhai"
        lines = [
            f"{target}, tu wo insaan hai jisko dekh kar Google Map bhi bol de 'Rasta badal lo' 😂",
            f"{target}, tera presence dekh kar Wi-Fi ke signal bhi weak ho jate hain 💀",
            f"{target}, agar bewakoofi Olympic game hoti to tu gold medal leke baitha hota 🥇",
        ]
        await reply_card(uclient, event, fun_card("🔥 SAVAGE ROAST", random.choice(lines)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.party$"))
    async def party_cmd(event):
        amt = random.randint(1500, 6000)
        await reply_card(uclient, event, fun_card("🍕 PARTY TREAT SCAN", f"Total Expense → ₹{amt}\nWallet Status → Sirf 10 ka purana sikka hai\nVerdict → Bill aate hi washroom bhaagne ki planning hai! 🏃"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.aukaat(?: (.+))?$"))
    async def aukaat_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        balances = [
            "₹14 in Paytm Wallet 💀",
            "₹2.50 (Dukan wale ka udhaar baaki hai) 😂",
            "₹50,000 (Chupke se FD todi hai) 😎",
            "Kangaroo ke jeb se bhi zyada khali 🦘",
            "Ambani level virtual confidence 👑",
        ]
        await reply_card(uclient, event, fun_card("💰 AUKAAT CHECKER", f"Target → {target}\nNet Worth → {random.choice(balances)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.nalla(?: (.+))?$"))
    async def nalla_cmd(event):
        target = event.pattern_match.group(1) or "Target"
        p = random.randint(50, 100)
        skills = [
            "14 ghante bistar pe lete rehna 🛌",
            "Chhat ke pankhe ke chakkar ginna 🌀",
            "Har 5 minute me fridge khol ke dekhna 🧊",
            "Bina baat ke WhatsApp status dekhna 📱",
        ]
        await reply_card(uclient, event, fun_card("🛌 NALLAPAN METER", f"Candidate → {target}\nBerozgari Level → {p}%\nSpecial Skill → {random.choice(skills)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pyaar$"))
    async def pyaar_cmd(event):
        outcomes = [
            "\"Aap bohot acche ho par main aapko bhai maanti hu\" 💔 F in the chat!",
            "\"Mummy nahi manengi, caste alag hai hamari\" 😭",
            "\"Message seen par chhod diya (Blue ticks only)\" 💀",
            "\"Haan main bhi tumse pyaar karti hu! (Sapne se jaago)\" 😂",
            "Congratulations! Block list me add ho gaye ho 🚫",
        ]
        await reply_card(uclient, event, fun_card("💌 PROPOSAL STATUS", random.choice(outcomes)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.shadi$"))
    async def shadi_cmd(event):
        dahej = [
            "Ek purana Bajaj Chetak scooter 🛵",
            "Sonpapdi ka 4 saal purana dabba 🍬",
            "2 plate chole bhature treat 🍽️",
            "Sirf ashirwad aur duaayein 🤲",
        ]
        await reply_card(uclient, event, fun_card("👰 SHADI KUNDALI", f"Band-Baaja → Taiyaar hai 🎺\nDahej Package → {random.choice(dahej)}\nVerdict → Rishta pakka!"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.bhabhi$"))
    async def bhabhi_cmd(event):
        results = [
            "Radar scanning... Bhabhi mil gayi par wo tumhare dost ke sath ghum rahi hai 😂",
            "404: Bhabhi not found, kripya pehle shakal sudhaarein 💀",
            "Bhabhi line maar rahi hai... Jaldi DM check karo! 😉",
            "Bhabhi ji to kisi aur ki ho gayi, next try karo! 💔",
        ]
        await reply_card(uclient, event, fun_card("📡 BHABHI FINDER RADAR", random.choice(results)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.iq(?: (.+))?$"))
    async def iq_cmd(event):
        target = event.pattern_match.group(1) or "Your"
        val = random.randint(10, 200)
        remark = "🧠 Albert Einstein Mode!" if val > 150 else "⚡ Smart Brain" if val > 100 else "💡 Tubelight detected!"
        await reply_card(uclient, event, fun_card("🧠 IQ SCANNER", f"Target → {target}\nCalculated IQ → {val}\nVerdict → {remark}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dost(?: (.+))?$"))
    async def dost_cmd(event):
        target = event.pattern_match.group(1) or "Friend"
        p = random.randint(1, 100)
        remark = "Momos ke liye jaan de dega! 🤝" if p > 80 else "Zaroorat padne par offline ho jayega 😂" if p < 40 else "Solid yaari!"
        await reply_card(uclient, event, fun_card("👬 JIGRI YAAR METER", f"Buddy → {target}\nBonding → {p}%\nVerdict → {remark}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.crime$"))
    async def crime_cmd(event):
        crimes = [
            ("Raat ko 3 baje tak reels scroll karna 📱", "Saza: 2 din bina internet ke"),
            ("Bina homework kiye so jana 😴", "Saza: Bartan dhona padega"),
            ("Momos akele akele kha lena 🥟", "Saza: Dosto ko treat dena"),
            ("Call kaat ke bolna 'battery low thi' 😂", "Saza: 1 ghanta lecture sunna"),
        ]
        c, s = random.choice(crimes)
        await reply_card(uclient, event, fun_card("🚔 POLICE RECORD SCAN", f"Crime → {c}\nSaza → {s}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.future$"))
    async def future_cmd(event):
        futures = [
            "Tapri pe chai peete hue coding karna 💻☕",
            "Himalaya me sant ban jana 🧘‍♂️",
            "Dubai me Lamborghini ghumana 🏎️",
            "Shaadi ke baad bartan maanjhna 🧼",
            "Bada tech startup kholna 🚀",
        ]
        await reply_card(uclient, event, fun_card("🔮 5-YEAR CAREER PREDICTION", f"Result → {random.choice(futures)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.gf$"))
    async def gf_cmd(event):
        n = random.choice([0, 0, 0, 1, 2, 7])
        verdict = "Single hi marega bhai tu 😂" if n == 0 else "Playboy level swag 😎" if n > 2 else "Ek hi kaafi hai!"
        await reply_card(uclient, event, fun_card("💔 GF COUNTER SCAN", f"Count → {n}\nStatus → {verdict}"), collapsed=True)

    # ----------------- GAMES & TOOLS -----------------
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.truth$"))
    async def truth_cmd(event):
        truths = [
            "Aapka sabse ajeeb secret kya hai?",
            "Last time jhooth kisko aur kyu bola tha?",
            "Aapka secret crush kaun hai?",
            "Aapne aakhri baar phone kab chupaya tha?",
        ]
        await reply_card(uclient, event, fun_card("🗣️ TRUTH CHALLENGE", random.choice(truths)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dare$"))
    async def dare_cmd(event):
        dares = [
            "Apne bio me agle 1 ghante ke liye 'I Love Momos' likho!",
            "Kisi random friend ko call karke bolna 'Mujhe sab pata chal gaya hai' fir kaat dena!",
            "Apni sabse purani gallery photo display picture lagao!",
            "Kisi ko voice note me funny song gaa ke bhejo!",
        ]
        await reply_card(uclient, event, fun_card("🎯 DARE CHALLENGE", random.choice(dares)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pass(?: (\d+))?$"))
    async def pass_cmd(event):
        arg = event.pattern_match.group(1)
        length = int(arg) if arg and arg.isdigit() and 8 <= int(arg) <= 32 else 12
        chars = string.ascii_letters + string.digits + "!@#$%^&*"
        pwd = "".join(random.choice(chars) for _ in range(length))
        await reply_card(uclient, event, fun_card("🔐 SECURE PASSWORD GENERATOR", f"`{pwd}`\n\n_Tap to copy safe key._"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.toss$"))
    async def toss_cmd(event):
        side = random.choice(["HEADS", "TAILS"])
        decision = random.choice(["Batting 🏏", "Bowling ⚾"])
        await reply_card(uclient, event, fun_card("🪙 CRICKET TOSS", f"Coin flipped → **{side}**\nDecision → Choose to **{decision}** first!"), collapsed=True)

    JOKES = [
        "My Wi‑Fi and I broke up. There was no connection. 😂",
        "404: Motivation not found. 💀",
        "My code works. I have no idea why. 😭",
    ]
    ROASTS = [
        "Tera confidence 5G hai, logic abhi 2G. 😂",
        "Swag HD, planning 144p. 💀",
        "Tera brain loading screen pe atka hai. 😭",
    ]
    FACTS = [
        "Honey never spoils. Archaeologists have found edible honey in ancient Egyptian tombs.",
        "Octopuses have three hearts and blue blood.",
        "Bananas are curved because they grow towards the sun.",
    ]
    QUOTES = [
        "Do what you can, with what you have, where you are.",
        "Simplicity is the soul of efficiency.",
        "Talk is cheap. Show me the code.",
    ]

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.joke$"))
    async def joke_cmd(event):
        await reply_card(uclient, event, fun_card("😂 JOKE", random.choice(JOKES)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.roast$"))
    async def roast_cmd(event):
        await reply_card(uclient, event, fun_card("🔥 ROAST", random.choice(ROASTS)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.fact$"))
    async def fact_cmd(event):
        await reply_card(uclient, event, fun_card("🧠 FACT", random.choice(FACTS)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.quote$"))
    async def quote_cmd(event):
        await reply_card(uclient, event, fun_card("📜 QUOTE", random.choice(QUOTES)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.love(?: (.+))?$"))
    async def love_cmd(event):
        name = event.pattern_match.group(1) or "You"
        p = random.randint(1, 100)
        res = "💖 PERFECT MATCH" if p >= 85 else "💕 Looking good" if p >= 60 else "😂 Better luck next time"
        await reply_card(uclient, event, fun_card("❤️ LOVE SCANNER", f"Target → {name}\nCompatibility → {p}%\n\n{res}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.crush$"))
    async def crush_cmd(event):
        p = random.randint(1, 100)
        res = "🔥 They might like you!" if p >= 70 else "👀 Suspicious..." if p >= 40 else "💀 Move on."
        await reply_card(uclient, event, fun_card("💘 CRUSH DETECTOR", f"Chance → {p}%\n\n{res}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.marry(?: (.+))?$"))
    async def marry_cmd(event):
        name = event.pattern_match.group(1) or "Partner"
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("💍 MARRIAGE METER", f"Target → {name}\nChances → {p}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.friend$"))
    async def friend_cmd(event):
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🤝 FRIENDSHIP METER", f"Loyalty Level → {p}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.aura$"))
    async def aura_cmd(event):
        n = random.randint(1, 9999)
        res = "👑 MAIN CHARACTER" if n >= 8000 else "🔥 Strong aura" if n >= 5000 else "😂 Need more aura"
        await reply_card(uclient, event, fun_card("🥶 AURA CHECK", f"Aura → +{n}\n\n{res}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sigma$"))
    async def sigma_cmd(event):
        n = random.randint(1, 100)
        res = "🗿 FINAL BOSS" if n >= 90 else "🔥 Sigma grind" if n >= 60 else "😂 Tutorial mode"
        await reply_card(uclient, event, fun_card("🗿 SIGMA CHECK", f"Sigma Level → {n}%\n\n{res}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.sus$"))
    async def sus_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🚨 SUSPICION METER", f"Suspicious Level → {n}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.evil$"))
    async def evil_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("😈 EVIL METER", f"Villain Score → {n}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rich$"))
    async def rich_cmd(event):
        n = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("💰 WEALTH METER", f"Virtual Riches → {n}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rank$"))
    async def rank_cmd(event):
        ranks = ["Bronze", "Silver", "Gold", "Platinum", "Diamond", "Crown", "Ace", "Conqueror"]
        await reply_card(uclient, event, fun_card("🎖️ RANK STATUS", f"Current Rank → {random.choice(ranks)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.mood$"))
    async def mood_cmd(event):
        moods = ["Happy 😄", "Lazy 😴", "Chad 🗿", "Hyped ⚡", "Chill 🏖️", "Hungry 🍕"]
        await reply_card(uclient, event, fun_card("🎭 MOOD DETECTOR", f"Vibe → {random.choice(moods)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rate(?: (.+))?$"))
    async def rate_cmd(event):
        thing = event.pattern_match.group(1) or "This"
        r = random.randint(1, 10)
        await reply_card(uclient, event, fun_card("⭐ RATING", f"Subject → {thing}\nScore → {r}/10"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.luck$"))
    async def luck_cmd(event):
        p = random.randint(1, 100)
        await reply_card(uclient, event, fun_card("🍀 LUCK METER", f"Luck Today → {p}%"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.predict$"))
    async def predict_cmd(event):
        outcomes = ["Sab sahi hoga!", "Chances kam hain.", "Bilkul pakka!", "Thoda wait karo."]
        await reply_card(uclient, event, fun_card("🔮 PREDICTION", random.choice(outcomes)), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.8ball(?: (.+))?$"))
    async def eightball_cmd(event):
        q = event.pattern_match.group(1) or "Question"
        ans = ["Yes definitely.", "No way.", "Ask again later.", "Outlook good.", "Doubtful."]
        await reply_card(uclient, event, fun_card("🎱 MAGIC 8-BALL", f"Q: {q}\nA: {random.choice(ans)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.choose(?: (.+))?$"))
    async def choose_cmd(event):
        raw = event.pattern_match.group(1)
        if not raw or "|" not in raw:
            await reply_card(uclient, event, "⚠️ Usage: `.choose Option A | Option B | Option C`", collapsed=False)
            return
        options = [x.strip() for x in raw.split("|") if x.strip()]
        await reply_card(uclient, event, fun_card("🎯 DECISION MAKER", f"Selected → **{random.choice(options)}**"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.dice$"))
    async def dice_cmd(event):
        await reply_card(uclient, event, fun_card("🎲 DICE ROLL", f"Result → {random.randint(1, 6)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.flip$"))
    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.coin$"))
    async def coin_cmd(event):
        await reply_card(uclient, event, fun_card("🪙 COIN TOSS", f"Outcome → {random.choice(['🟡 HEADS', '⚪ TAILS'])}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.rps(?: (.+))?$"))
    async def rps_cmd(event):
        user_choice = event.pattern_match.group(1)
        bot_choice = random.choice(["Rock 🪨", "Paper 📄", "Scissors ✂️"])
        body = f"My Pick → {bot_choice}" + (f"\nYour Pick → {user_choice}" if user_choice else "")
        await reply_card(uclient, event, fun_card("✂️ ROCK PAPER SCISSORS", body), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.slot$"))
    async def slot_cmd(event):
        emojis = ["🍒", "🍋", "🍇", "🍉", "⭐", "🔔", "7️⃣"]
        line = [random.choice(emojis) for _ in range(3)]
        win = "🎉 JACKPOT!" if line[0] == line[1] == line[2] else "Try again!"
        await reply_card(uclient, event, fun_card("🎰 SLOT MACHINE", f"[ {' | '.join(line)} ]\n\n{win}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.number$"))
    async def number_cmd(event):
        await reply_card(uclient, event, fun_card("🔢 LUCKY NUMBER", f"Number → {random.randint(1, 100)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.guess$"))
    async def guess_cmd(event):
        await reply_card(uclient, event, fun_card("❓ GUESS CHALLENGE", f"Guess between 1 and 10! Answer: {random.randint(1, 10)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.trivia$"))
    async def trivia_cmd(event):
        trivias = [
            ("Which planet is closest to the sun?", "Mercury"),
            ("What is the capital of Japan?", "Tokyo"),
            ("How many continents are there?", "7"),
        ]
        q, a = random.choice(trivias)
        await reply_card(uclient, event, fun_card("💡 MINI TRIVIA", f"Question: {q}\nAnswer: {a}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.animal$"))
    async def animal_cmd(event):
        animals = ["🦁 Lion", "🐯 Tiger", "🐼 Panda", "🦅 Eagle", "🐺 Wolf", "🦊 Fox"]
        await reply_card(uclient, event, fun_card("🐾 RANDOM ANIMAL", f"Spawned: {random.choice(animals)}"), collapsed=True)

    @uclient.on(events.NewMessage(outgoing=True, pattern=r"^\.pick$"))
    async def pick_cmd(event):
        colors = ["🔴 Crimson Red", "🔵 Sapphire Blue", "🟢 Emerald Green", "🟡 Golden Yellow", "🟣 Royal Purple"]
        await reply_card(uclient, event, fun_card("🎨 COLOR PICKER", f"Picked: {random.choice(colors)}"), collapsed=True)

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

    # Cache Bot info to make /start instant
    try:
        me = await bot.get_me()
        CACHED_BOT_INFO["username"] = me.username or "Ashishxophsjs_bot"
        CACHED_BOT_INFO["display_name"] = me.first_name or "ASHISH BOT"
    except Exception:
        pass

    # Pre-cache media setting from Mongo on start
    doc_media = await settings_col.find_one({"key": "welcome_media_id"})
    if doc_media:
        if doc_media.get("type") == "photo":
            CACHED_MEDIA["type"] = "photo"
            CACHED_MEDIA["path"] = PHOTO_CACHE_PATH
        elif doc_media.get("type") == "video":
            CACHED_MEDIA["type"] = "video"
            CACHED_MEDIA["path"] = VIDEO_CACHE_PATH

    await load_saved_sessions()
    print("All subsystems running perfectly.")

    asyncio.create_task(log_to_channel(f"⚡ **{BRAND} Server Re-deployed & Online!**"))

    await bot.run_until_disconnected()

if __name__ == "__main__":
    asyncio.run(main())
