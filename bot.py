import telebot
import re
import html
import logging

# ============================================================
# CONFIG
# ============================================================

BOT_TOKEN = "PASTE_NEW_BOT_TOKEN_HERE"

bot = telebot.TeleBot(
    BOT_TOKEN,
    parse_mode="HTML",
    threaded=True
)

BRAND = "@ShitijRips"

DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024

# ============================================================
# LOGGING
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("ISH_Renamer_Bot")

# ============================================================
# STORAGE
# ============================================================

ADMINS = set()
TARGET_CHATS = set()

# admin_id -> source chat ID / @username
FORWARD_SOURCES = {}

# admin_id -> target chat ID
FORWARD_GROUPS = {}

# admin_id -> True / False
FORWARD_RUNNING = {}

# ============================================================
# HELPERS
# ============================================================

def is_admin(user_id):
    return user_id in ADMINS


def extract_source_from_link(text):
    """
    Supports:

    https://t.me/channel/123
    https://t.me/channel
    https://t.me/c/1234567890/123
    """

    if not text:
        return None

    text = text.strip()

    # Private channel/group link
    match = re.search(
        r"(?:https?://)?t\.me/c/(\d+)/\d+",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return int("-100" + match.group(1))

    # Public channel/group
    match = re.search(
        r"(?:https?://)?t\.me/([A-Za-z0-9_]{4,})(?:/\d+)?",
        text,
        flags=re.IGNORECASE
    )

    if match:
        return "@" + match.group(1)

    return None


def get_forwarded_source(msg):
    """
    Detect source from a forwarded Telegram message.
    """

    if getattr(msg, "forward_from_chat", None):
        return msg.forward_from_chat.id

    # Newer Telegram forward origin
    origin = getattr(msg, "forward_origin", None)

    if origin:
        chat = getattr(origin, "chat", None)

        if chat:
            return chat.id

    return None


def source_matches(msg, source):
    if source is None:
        return False

    # Numeric source
    if isinstance(source, int):
        return msg.chat.id == source

    # Username source
    source_username = str(source).lstrip("@").lower()

    chat_username = getattr(
        msg.chat,
        "username",
        None
    )

    if not chat_username:
        return False

    return chat_username.lower() == source_username


# ============================================================
# CLEAN CAPTION
# ============================================================

def clean_caption(original):
    if not original:
        original = "Video.mp4"

    text = str(original).strip()

    # Remove normal links
    # Keep t.me links
    text = re.sub(
        r"https?://(?!t\.me/)\S+",
        "",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Replace known source names
    # --------------------------------------------------------

    text = re.sub(
        r"(?i)"
        r"(tvshowhub|"
        r"tvshow|"
        r"hub|"
        r"bhavik611|"
        r"mrxvoltz|"
        r"srp_main_channel|"
        r"srbrips|"
        r"SARDAR\.\&\.MHDZubair|"
        r"AJK-BOY\.\&\.MHDZubair|"
        r"Cinevood|"
        r"SRBRipx_Official|"
        r"PMTV4|"
        r"DG_Contents)",
        "Shitij",
        text
    )

    # --------------------------------------------------------
    # [@anything] -> [@ShitijRips]
    # --------------------------------------------------------

    text = re.sub(
        r"\[@[^\]]*\]",
        f"[{BRAND}]",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Replace usernames
    # --------------------------------------------------------

    text = re.sub(
        r"@[A-Za-z0-9_]{3,}",
        BRAND,
        text
    )

    # --------------------------------------------------------
    # Remove unwanted promo/owner lines
    # --------------------------------------------------------

    spam_patterns = [
        r"owner.*",
        r"first.*telegram.*",
        r"exclusive.*",
        r"☎.*",
        r"contact.*",
        r"follow.*",
        r"powered.*",
        r"uploaded.*",
        r"by.*",
        r"[━─]{3,}",
        r"❤️.*",
        r"🌹.*",
        r"🌺.*",
        r"💥.*",
    ]

    for pattern in spam_patterns:
        text = re.sub(
            pattern,
            "",
            text,
            flags=re.IGNORECASE
        )

    # --------------------------------------------------------
    # Remove duplicate Shitij
    # --------------------------------------------------------

    text = re.sub(
        r"(?:Shitij[\s._-]*){2,}",
        "Shitij",
        text,
        flags=re.IGNORECASE
    )

    # --------------------------------------------------------
    # Lines
    # --------------------------------------------------------

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    filename = lines[0] if lines else "Video.mp4"

    # --------------------------------------------------------
    # Clean filename separators
    # --------------------------------------------------------

    filename = re.sub(
        r"[\s/]+",
        ".",
        filename
    )

    filename = filename.strip(" ._-")

    if not filename:
        filename = "Video.mp4"

    # --------------------------------------------------------
    # Ensure extension
    # --------------------------------------------------------

    if not filename.lower().endswith(
        (".mp4", ".mkv", ".avi")
    ):
        filename += ".mp4"

    # --------------------------------------------------------
    # Final caption
    # --------------------------------------------------------

    caption = (
        f"<code>{html.escape(filename)}</code>\n\n"
        f"💝Join Our Main Channel : {BRAND}💥"
    )

    return caption[:TELEGRAM_CAPTION_LIMIT]


# ============================================================
# MEDIA HELPERS
# ============================================================

def get_media_info(msg):

    if (
        msg.content_type == "video"
        and getattr(msg, "video", None)
    ):
        return (
            msg.video.file_id,
            msg.caption or msg.video.file_name,
            "video"
        )

    if (
        msg.content_type == "document"
        and getattr(msg, "document", None)
    ):
        return (
            msg.document.file_id,
            msg.caption or msg.document.file_name,
            "document"
        )

    return None


def send_media(chat_id, msg, caption):

    info = get_media_info(msg)

    if not info:
        return False

    file_id, _, media_type = info

    try:

        if media_type == "video":

            bot.send_video(
                chat_id,
                file_id,
                caption=caption,
                supports_streaming=True
            )

        else:

            bot.send_document(
                chat_id,
                file_id,
                caption=caption
            )

        return True

    except Exception as e:

        logger.warning(
            "Media send failed | chat=%s | error=%s",
            chat_id,
            e
        )

        return False


# ============================================================
# START
# ============================================================

@bot.message_handler(commands=["start"])
def start(msg):

    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "📌 Send any video/document, I'll:\n\n"
        "✅ Clean filename/caption\n"
        "✅ Add @ShitijRips\n"
        "✅ Send to target chats\n"
        "✅ Send to dump channel\n\n"
        "📁 Videos/documents only."
    )


# ============================================================
# ADD ADMIN
# ============================================================

@bot.message_handler(commands=["addadmin"])
def add_admin(msg):

    ADMINS.add(msg.from_user.id)

    bot.reply_to(
        msg,
        f"✅ Admin added: "
        f"<code>{msg.from_user.id}</code>"
    )


# ============================================================
# WHERE ADMIN
# ============================================================

@bot.message_handler(commands=["whereadmin"])
def where_admin(msg):

    if not is_admin(msg.from_user.id):

        bot.reply_to(
            msg,
            "❌ You are not an admin."
        )

        return

    if not TARGET_CHATS:

        bot.reply_to(
            msg,
            "🤖 Bot is not admin/member anywhere."
        )

        return

    text = "<b>📋 Bot present in:</b>\n\n"

    for chat_id in sorted(TARGET_CHATS):

        text += f"• <code>{chat_id}</code>\n"

    bot.reply_to(
        msg,
        text
    )


# ============================================================
# START FORWARD
# ============================================================

@bot.message_handler(commands=["forward"])
def start_forward(msg):

    if not is_admin(msg.from_user.id):

        bot.reply_to(
            msg,
            "❌ You are not an admin."
        )

        return

    admin_id = msg.from_user.id

    FORWARD_RUNNING[admin_id] = False

    FORWARD_SOURCES.pop(
        admin_id,
        None
    )

    FORWARD_GROUPS.pop(
        admin_id,
        None
    )

    bot.reply_to(
        msg,
        "❪ SET SOURCE CHAT ❫\n\n"
        "1️⃣ Forward any message from source chat here\n"
        "OR send its t.me message link.\n\n"
        "2️⃣ Set target:\n"
        "<code>/setgroup -1001234567890</code>\n\n"
        "3️⃣ Forwarding will start automatically.\n\n"
        "❌ /cancel = cancel"
    )


# ============================================================
# SET GROUP
# ============================================================

@bot.message_handler(commands=["setgroup"])
def set_group(msg):

    if not is_admin(msg.from_user.id):

        bot.reply_to(
            msg,
            "❌ You are not an admin."
        )

        return

    parts = msg.text.split(
        maxsplit=1
    )

    if len(parts) != 2:

        bot.reply_to(
            msg,
            "❌ Usage:\n"
            "<code>/setgroup -1001234567890</code>"
        )

        return

    try:

        group_id = int(
            parts[1].strip()
        )

    except ValueError:

        bot.reply_to(
            msg,
            "❌ Invalid chat ID.\n"
            "Example: <code>-1001234567890</code>"
        )

        return

    admin_id = msg.from_user.id

    if admin_id not in FORWARD_SOURCES:

        bot.reply_to(
            msg,
            "❌ First use /forward "
            "and set the source."
        )

        return

    FORWARD_GROUPS[admin_id] = group_id

    FORWARD_RUNNING[admin_id] = True

    bot.reply_to(
        msg,
        f"✅ Target set:\n"
        f"<code>{group_id}</code>\n\n"
        f"🟢 Auto-forwarding started."
    )


# ============================================================
# CANCEL
# ============================================================

@bot.message_handler(commands=["cancel"])
def cancel_forward(msg):

    if not is_admin(msg.from_user.id):

        bot.reply_to(
            msg,
            "❌ You are not an admin."
        )

        return

    admin_id = msg.from_user.id

    FORWARD_SOURCES.pop(
        admin_id,
        None
    )

    FORWARD_GROUPS.pop(
        admin_id,
        None
    )

    FORWARD_RUNNING[admin_id] = False

    bot.reply_to(
        msg,
        "❌ Forwarding process cancelled."
    )


# ============================================================
# CAPTURE SOURCE
# ============================================================

def capture_source(msg):

    admin_id = msg.from_user.id

    if not is_admin(admin_id):
        return

    # Only capture while /forward setup is active
    if admin_id not in FORWARD_RUNNING:
        return

    # Already running
    if FORWARD_RUNNING.get(
        admin_id,
        False
    ):
        return

    source = get_forwarded_source(msg)

    # If not forwarded message, check link
    if source is None and msg.text:

        source = extract_source_from_link(
            msg.text
        )

    if source is None:

        bot.reply_to(
            msg,
            "❌ Source not detected.\n\n"
            "Forward a message from source "
            "or send a valid t.me link."
        )

        return

    FORWARD_SOURCES[admin_id] = source

    bot.reply_to(
        msg,
        f"✅ Source set:\n"
        f"<code>{html.escape(str(source))}</code>\n\n"
        f"Now use:\n"
        f"<code>/setgroup -1001234567890</code>"
    )


# ============================================================
# MEDIA HANDLER
# ============================================================

@bot.message_handler(
    content_types=[
        "video",
        "document"
    ]
)
def handle_media(msg):

    if not is_admin(msg.from_user.id):

        bot.reply_to(
            msg,
            "❌ You are not authorized "
            "to use this bot."
        )

        return

    info = get_media_info(msg)

    if not info:
        return

    _, original_name, _ = info

    caption = clean_caption(
        original_name
    )

    # Send to original chat
    send_media(
        msg.chat.id,
        msg,
        caption
    )

    # Send to all configured target chats
    for chat_id in list(TARGET_CHATS):

        if chat_id == msg.chat.id:
            continue

        send_media(
            chat_id,
            msg,
            caption
        )

    # Send to dump channel
    if DUMP_CHANNEL_ID != msg.chat.id:

        send_media(
            DUMP_CHANNEL_ID,
            msg,
            caption
        )


# ============================================================
# AUTO FORWARD
# ============================================================

@bot.message_handler(
    content_types=[
        "video",
        "document",
        "text"
    ]
)
def auto_forward(msg):

    if not msg.chat:
        return

    for admin_id, source in list(
        FORWARD_SOURCES.items()
    ):

        if not FORWARD_RUNNING.get(
            admin_id,
            False
        ):
            continue

        target = FORWARD_GROUPS.get(
            admin_id
        )

        if not target:
            continue

        if not source_matches(
            msg,
            source
        ):
            continue

        try:

            # Video/document
            if msg.content_type in (
                "video",
                "document"
            ):

                info = get_media_info(msg)

                if not info:
                    continue

                _, original_name, _ = info

                caption = clean_caption(
                    original_name
                )

                send_media(
                    target,
                    msg,
                    caption
                )

            # Text
            elif msg.content_type == "text":

                if msg.text:

                    bot.send_message(
                        target,
                        msg.text
                    )

        except Exception as e:

            logger.warning(
                "Auto-forward error | "
                "admin=%s | source=%s | "
                "target=%s | error=%s",
                admin_id,
                source,
                target,
                e
            )


# ============================================================
# SOURCE LINK / MESSAGE SETUP
# ============================================================

@bot.message_handler(
    func=lambda m: (
        m.content_type == "text"
        and not (m.text or "").startswith("/")
    )
)
def source_capture_text(msg):

    capture_source(msg)


# ============================================================
# TRACK BOT CHATS
# ============================================================

@bot.my_chat_member_handler()
def track(update):

    try:

        chat_id = update.chat.id

        status = update.new_chat_member.status

        if status in (
            "administrator",
            "member"
        ):

            TARGET_CHATS.add(
                chat_id
            )

            logger.info(
                "Bot active in chat: %s",
                chat_id
            )

        else:

            TARGET_CHATS.discard(
                chat_id
            )

    except Exception as e:

        logger.warning(
            "Chat tracking error: %s",
            e
        )


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    print(
        "🤖 ISH Renamer Bot + "
        "Forward Feature running..."
    )

    bot.infinity_polling(
        skip_pending=True,
        allowed_updates=[
            "message",
            "my_chat_member"
        ]
)
