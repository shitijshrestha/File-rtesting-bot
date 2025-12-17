import telebot
import re
import html

# ---------------- CONFIG ---------------- #

BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BRAND = "@ShitijRips"

ADMINS = set()
TARGET_CHATS = set()

DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024


# ---------------- CLEAN FUNCTION ---------------- #

def clean_caption(original: str) -> str:
    if not original:
        original = "Video.mp4"

    # Remove normal links but keep t.me
    text = re.sub(r"https?://(?!t\.me)\S+", "", original)

    # Replace known source names
    text = re.sub(
        r"(?i)(tvshowhub|tvshow|hub|bhavik611|mrxvoltz|srp_main_channel|srbrips)",
        "Shitij",
        text,
    )

    # Replace [@anything] → [@ShitijRips]
    text = re.sub(r"\[@[^]]*\]", f"[{BRAND}]", text, flags=re.IGNORECASE)

    # Replace all @usernames
    text = re.sub(r"@\w+", BRAND, text)

    # Remove owner / spam / promo lines
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
    for p in spam_patterns:
        text = re.sub(p, "", text, flags=re.IGNORECASE)

    # Remove duplicate Shitij
    text = re.sub(r"(Shitij)+", "Shitij", text)

    # Split lines
    lines = [l.strip() for l in text.splitlines() if l.strip()]

    filename = lines[0]

    # Clean separators
    filename = re.sub(r"[\s/]+", ".", filename).strip(" .")

    # Force brand at end
    filename = re.sub(
        r"-@?\w+(\.\w+)$",
        rf"-{BRAND}\1",
        filename
    )

    # Ensure extension
    if not filename.lower().endswith((".mp4", ".mkv", ".avi")):
        filename += ".mp4"

    caption = (
        f"<code>{html.escape(filename)}</code>\n\n"
        f"💝Join Our Main Channel : {BRAND}💥"
    )

    return caption[:TELEGRAM_CAPTION_LIMIT]


# ---------------- COMMANDS ---------------- #

@bot.message_handler(commands=["start"])
def start(msg):
    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "📌 Send any video/document, I'll:\n\n"
        "✅ Works for videos/documents only."
    )


@bot.message_handler(commands=["addadmin"])
def add_admin(msg):
    ADMINS.add(msg.from_user.id)
    bot.reply_to(msg, f"✅ Admin added: <code>{msg.from_user.id}</code>")


@bot.message_handler(commands=["whereadmin"])
def where_admin(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only.")
        return

    if not TARGET_CHATS:
        bot.reply_to(msg, "🤖 Bot is not admin anywhere.")
        return

    text = "<b>📋 Bot present in:</b>\n\n"
    for cid in TARGET_CHATS:
        text += f"• <code>{cid}</code>\n"
    bot.reply_to(msg, text)


# ---------------- MEDIA HANDLER ---------------- #

@bot.message_handler(content_types=["video", "document"])
def handle_media(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only. Use /addadmin")
        return

    if msg.content_type == "video":
        file_id = msg.video.file_id
        src = msg.caption or msg.video.file_name
        send = bot.send_video
        extra = {"supports_streaming": True}
    else:
        file_id = msg.document.file_id
        src = msg.caption or msg.document.file_name
        send = bot.send_document
        extra = {}

    caption = clean_caption(src)

    send(msg.chat.id, file_id, caption=caption, **extra)

    for chat in TARGET_CHATS:
        try:
            send(chat, file_id, caption=caption, **extra)
        except:
            pass

    try:
        send(DUMP_CHANNEL_ID, file_id, caption=caption, **extra)
    except:
        pass


# ---------------- TRACK GROUPS ---------------- #

@bot.my_chat_member_handler()
def track(update):
    chat_id = update.chat.id
    status = update.new_chat_member.status

    if status in ["administrator", "member"]:
        TARGET_CHATS.add(chat_id)
    else:
        TARGET_CHATS.discard(chat_id)


# ---------------- RUN ---------------- #

print("🤖 ISH Renamer Bot running (ALL FEATURES MERGED)")
bot.infinity_polling(skip_pending=True)
