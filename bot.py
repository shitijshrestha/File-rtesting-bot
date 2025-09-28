import telebot
import re
import html

# --- Bot Token ---
BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- Admins & Targets ---
ADMINS = set()       # admin user_ids
TARGET_CHATS = set() # groups/channels where bot is admin
TELEGRAM_CAPTION_LIMIT = 1024  # Telegram max caption length

# --- Helper Function ---
def clean_filename(original: str) -> str:
    if not original:
        original = "Video.mp4"

    # Remove all links
    no_links = re.sub(r"(https?://\S+|t\.me/\S+|\S+\.com\S*)", "", original)

    # Replace all target names → Shitij
    replaced = re.sub(r"(?i)(tvshowhub|tvshow|hub|bhavik611|mrxvoltz|srp_main_channel)", "Shitij", no_links)

    # Remove repeated Shitij
    replaced = re.sub(r"(Shitij)+", "Shitij", replaced)

    # Replace spaces/slashes with dot
    cleaned = re.sub(r"[\s/]+", ".", replaced).strip(" .")

    # Monospace + Telegram limit
    caption = f"<code>{html.escape(cleaned)}</code>"
    if len(caption) > TELEGRAM_CAPTION_LIMIT:
        caption = caption[:TELEGRAM_CAPTION_LIMIT-8] + "…</code>"

    return caption

# --- Command Handlers ---
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "📌 Send any video/document, I'll:\n"
        "   - Replace TvShowHub/Bhavik611/MRxVoltz/SRP_Main_Channel → Shitij\n"
        "   - Remove links (http, https, t.me, etc.)\n"
        "   - Keep full filename in Mono-Serif style\n"
        "   - Forward to channels/groups where bot is admin (sender hidden)\n\n"
        "✅ Works for all videos/documents."
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

# --- Video / Document Handler ---
@bot.message_handler(content_types=['video', 'document'])
def handle_media(msg):
    user_id = msg.from_user.id
    if user_id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only. Use /addadmin to become admin.")
        return

    if msg.content_type == 'video':
        original_name = msg.caption if msg.caption else msg.video.file_name
        file_id = msg.video.file_id
        file_size = msg.video.file_size
        send_func = bot.send_video
    else:
        original_name = msg.caption if msg.caption else msg.document.file_name
        file_id = msg.document.file_id
        file_size = msg.document.file_size
        send_func = bot.send_document

    new_caption = clean_filename(original_name)

    try:
        # Send back to sender
        if file_size < 2000 * 1024 * 1024:
            send_func(msg.chat.id, file_id, caption=new_caption, parse_mode="HTML", supports_streaming=True)
        else:
            send_func(msg.chat.id, file_id, caption=new_caption, parse_mode="HTML")

        # Forward to all admin channels/groups
        for target in TARGET_CHATS:
            try:
                if file_size < 2000 * 1024 * 1024:
                    send_func(target, file_id, caption=new_caption, parse_mode="HTML", supports_streaming=True)
                else:
                    send_func(target, file_id, caption=new_caption, parse_mode="HTML")
            except Exception as e:
                print(f"⚠️ Failed to send to {target}: {e}")

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error sending: {e}")

# --- Track Groups/Channels where bot is admin ---
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
print("🤖 ISH Bot running with full captions, Shitij rename & admin forwarding...")
bot.infinity_polling()