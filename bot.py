import telebot
import re
import html

# --- Bot Token ---
BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- Admins & Targets ---
ADMINS = set()       # user_ids who are admins
TARGET_CHATS = set() # groups/channels where bot is admin
TELEGRAM_CAPTION_LIMIT = 1024  # Telegram max caption length

# --- Helper Function ---
def clean_filename(original: str) -> str:
    if not original:
        original = "Video.mp4"

    # Remove plain links from filename (but keep join links in caption)
    no_links = re.sub(r"(https?://\S+)", "", original)

    # Replace unwanted names → Shitij
    replaced = re.sub(
        r"(?i)(tvshowhub|tvshow|hub|bhavik611|mrxvoltz|srp_main_channel|srbrips)",
        "Shitij",
        no_links,
    )

    # Replace "[@SRBRips]" with "[@ShitijRips]" (keep links safe)
    replaced = re.sub(r"\[@[^]]*\]", "[@ShitijRips]", replaced, flags=re.IGNORECASE)

    # Remove duplicate Shitij
    replaced = re.sub(r"(Shitij)+", "Shitij", replaced)

    # Replace spaces/slashes → dot
    cleaned = re.sub(r"[\s/]+", ".", replaced).strip(" .")

    # Monospace style caption
    caption = f"<code>{html.escape(cleaned)}</code>"
    if len(caption) > TELEGRAM_CAPTION_LIMIT:
        caption = caption[: TELEGRAM_CAPTION_LIMIT - 8] + "…</code>"

    return caption

# --- Commands ---
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "📌 Send any video/document, I'll:\n"
        "   - Replace names → Shitij\n"
        "   - Remove normal links in filename\n"
        "   - Convert [@anything] → [@ShitijRips]\n"
        "   - Keep Join links (https://t.me/...) safe\n"
        "   - Keep filename in monospace style\n"
        "   - Send to all groups/channels where bot is admin\n\n"
        "✅ Works for videos/documents only."
    )

@bot.message_handler(commands=['addadmin'])
def add_admin(msg):
    try:
        parts = msg.text.split()
        if len(parts) == 1:
            ADMINS.add(msg.from_user.id)
            bot.reply_to(msg, f"✅ You are now admin! (<code>{msg.from_user.id}</code>)")
            return
        new_admin = int(parts[1])
        ADMINS.add(new_admin)
        bot.reply_to(msg, f"✅ Added admin: <code>{new_admin}</code>")
    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error: {e}")

# --- Media Handler ---
@bot.message_handler(content_types=['video', 'document'])
def handle_media(msg):
    user_id = msg.from_user.id
    if user_id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only. Use /addadmin to become admin.")
        return

    if msg.content_type == 'video':
        original_name = msg.caption or msg.video.file_name
        file_id = msg.video.file_id
        send_func = bot.send_video
        extra_args = {"supports_streaming": True}
    else:
        original_name = msg.caption or msg.document.file_name
        file_id = msg.document.file_id
        send_func = bot.send_document
        extra_args = {}

    new_caption = clean_filename(original_name)

    try:
        # Send back to sender
        send_func(msg.chat.id, file_id, caption=new_caption, parse_mode="HTML", **extra_args)

        # Send to all admin groups/channels
        for target in TARGET_CHATS:
            try:
                send_func(target, file_id, caption=new_caption, parse_mode="HTML", **extra_args)
            except Exception as e:
                print(f"⚠️ Failed to send to {target}: {e}")

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error sending: {e}")

# --- Track groups/channels where bot is admin ---
@bot.my_chat_member_handler()
def track_groups_channels(update):
    chat = update.chat
    status = update.new_chat_member.status
    if status in ["administrator", "member"]:
        TARGET_CHATS.add(chat.id)
        print(f"✅ Bot is admin/member in: {chat.title or chat.id}")
    elif status in ["left", "kicked"]:
        TARGET_CHATS.discard(chat.id)
        print(f"❌ Bot removed from: {chat.title or chat.id}")

# --- Run Bot ---
print("🤖 ISH Bot running with Shitij renaming, caption cleaning & admin auto-forwarding...")

# ✅ Auto delete webhook before polling
bot.remove_webhook()

# ✅ Safe polling loop
bot.infinity_polling(skip_pending=True, timeout=20)
