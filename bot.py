import telebot
import re
import html

# ---------------- CONFIG ---------------- #

BOT_TOKEN = "8338489595:AAHPhsAj-SvbXlzdcB2mdPBNH6ch7Drot3I"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BRAND = "@ShitijRips"

ADMINS = set()
TARGET_CHATS = set()
DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024

# ---------------- FORWARD CONFIG ---------------- #
FORWARD_SOURCES = {}  # admin_id → source_chat (username/id)
FORWARD_GROUPS = {}   # admin_id → target group/channel id
FORWARD_RUNNING = {}  # admin_id → True/False

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
        bot.reply_to(msg, "❌ You are not an admin.")
        return

    if not TARGET_CHATS:
        bot.reply_to(msg, "🤖 Bot is not admin anywhere.")
        return

    text = "<b>📋 Bot present in:</b>\n\n"
    for cid in TARGET_CHATS:
        text += f"• <code>{cid}</code>\n"
    bot.reply_to(msg, text)

# ---------------- FORWARD FEATURE ---------------- #

@bot.message_handler(commands=["forward"])
def start_forward(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ You are not an admin.")
        return

    FORWARD_RUNNING[msg.from_user.id] = False
    bot.reply_to(
        msg,
        "❪ SET SOURCE CHAT ❫\n\n"
        "Forward the first/last message link of source chat.\n"
        "Then set target group using /setgroup <id>\n"
        "Use /cancel to cancel this process."
    )

@bot.message_handler(commands=["setgroup"])
def set_group(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ You are not an admin.")
        return
    try:
        group_id = int(msg.text.split(" ",1)[1])
        FORWARD_GROUPS[msg.from_user.id] = group_id
        FORWARD_RUNNING[msg.from_user.id] = True
        bot.reply_to(msg, f"✅ Target group set: {group_id}\nForwarding will start automatically.")
    except:
        bot.reply_to(msg, "❌ Usage: /setgroup -1001234567890")

@bot.message_handler(commands=["cancel"])
def cancel_forward(msg):
    FORWARD_SOURCES.pop(msg.from_user.id, None)
    FORWARD_GROUPS.pop(msg.from_user.id, None)
    FORWARD_RUNNING[msg.from_user.id] = False
    bot.reply_to(msg, "❌ Forwarding process cancelled.")

@bot.message_handler(func=lambda m: True)
def capture_source(msg):
    if msg.from_user.id not in ADMINS:
        return

    # Only process if user started /forward
    if msg.from_user.id not in FORWARD_RUNNING or FORWARD_RUNNING[msg.from_user.id]:
        return

    source_chat_id = None

    # If message is forwarded
    if msg.forward_from_chat:
        source_chat_id = msg.forward_from_chat.id
    # If t.me link
    elif msg.text and "t.me" in msg.text:
        match = re.search(r"t\.me/([a-zA-Z0-9_]+)/(\d+)", msg.text)
        if match:
            source_chat_id = match.group(1)

    if not source_chat_id:
        bot.reply_to(msg, "❌ Could not detect source. Forward a message or send message link.")
        return

    FORWARD_SOURCES[msg.from_user.id] = source_chat_id
    bot.reply_to(msg, f"✅ Source set: {source_chat_id}\nNow all new messages will be forwarded automatically.")

# ---------------- MEDIA HANDLER ---------------- #

@bot.message_handler(content_types=["video", "document"])
def handle_media(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ You are not authorized to use this bot.")
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

    # Send to original chat
    send(msg.chat.id, file_id, caption=caption, **extra)

    # Send to target chats
    for chat in TARGET_CHATS:
        try:
            send(chat, file_id, caption=caption, **extra)
        except:
            pass

    # Send to dump channel
    try:
        send(DUMP_CHANNEL_ID, file_id, caption=caption, **extra)
    except:
        pass

# ---------------- AUTO FORWARD FROM SET SOURCE ---------------- #

@bot.message_handler(content_types=["video","document","text"])
def auto_forward(msg):
    for admin_id, source in FORWARD_SOURCES.items():
        if not FORWARD_RUNNING.get(admin_id, False):
            continue

        target = FORWARD_GROUPS.get(admin_id)
        if not target:
            continue

        # Forward if message is from source chat
        if msg.chat.id == source or (isinstance(source,str) and getattr(msg.chat,"username","")==source):
            caption = ""
            if msg.content_type == "video":
                caption = clean_caption(msg.caption or msg.video.file_name)
                try:
                    bot.send_video(target, msg.video.file_id, caption=caption, supports_streaming=True)
                except: pass
            elif msg.content_type == "document":
                caption = clean_caption(msg.caption or msg.document.file_name)
                try:
                    bot.send_document(target, msg.document.file_id, caption=caption)
                except: pass
            else:
                try:
                    bot.send_message(target, msg.text)
                except: pass

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

print("🤖 ISH Renamer Bot + Forward Feature running")
bot.infinity_polling(skip_pending=True)
