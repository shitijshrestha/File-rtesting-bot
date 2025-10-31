import telebot
import re
import html

# --- Bot Token ---
BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

# --- Admins & Targets ---
ADMINS = set()
TARGET_CHATS = set()
DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024  # Telegram max caption length

# --- Helper Function ---
def clean_filename(original: str) -> str:
    """
    Cleans and formats any caption or filename.
    - Removes all non-Telegram links
    - Replaces any username, tag, group name, or text with 'Shitij' or [@ShitijRips]
    - Keeps Telegram join links (https://t.me/...) safe
    - Adds custom caption format
    """
    if not original:
        original = "Video.mp4"

    # Keep Telegram join links safe temporarily
    join_links = re.findall(r"(https?://t\.me/[^\s]+)", original)
    for i, link in enumerate(join_links):
        original = original.replace(link, f"__JOIN_LINK_{i}__")

    # Remove all other URLs
    no_links = re.sub(r"(https?://\S+)", "", original)

    # Replace every kind of @username or tag with [@ShitijRips]
    replaced = re.sub(r"@\w+", "[@ShitijRips]", no_links)

    # Replace known encoder/group words → Shitij
    replaced = re.sub(
        r"(?i)(hub|rips|encoded|encoder|by|official|content|channel|series|rip|webdl|upload|join|dmt|dg|jstar|mrn|mimam|tvshow|zee5|dangalplay|hotstar|sony|voot|ullu|prime|netflix|altbalaji|officialx|dg_rips|dmt_encod3s|dg_contents)",
        "Shitij",
        replaced,
    )

    # Fix duplicates (like ShitijShitij → Shitij)
    replaced = re.sub(r"(Shitij)+", "Shitij", replaced)

    # Replace slashes, newlines, or extra spaces with dots
    cleaned = re.sub(r"[\s/]+", ".", replaced).strip(" .")

    # Restore Telegram join links
    for i, link in enumerate(join_links):
        cleaned = cleaned.replace(f"__JOIN_LINK_{i}__", link)

    # Ensure it ends with -Shitij.mp4
    if not cleaned.lower().endswith(".mp4"):
        cleaned += ".mp4"
    if "-Shitij" not in cleaned:
        cleaned = cleaned.replace(".mp4", "-Shitij.mp4")

    # Build final caption format
    caption = (
        f"🔥 Upload By :- [@ShitijRips]\n"
        f"💥 Join 👉 https://t.me/ShitijRips\n\n"
        f"🎬 {html.escape(cleaned)}"
    )

    # Truncate caption if longer than Telegram limit
    if len(caption) > TELEGRAM_CAPTION_LIMIT:
        caption = caption[: TELEGRAM_CAPTION_LIMIT - 8] + "…"

    return caption


# --- Commands ---
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 Welcome to ISH Bot (Shitij Edition)!\n\n"
        "📌 Send any video or document — I'll:\n"
        "   • Replace all tags/usernames → Shitij / [@ShitijRips]\n"
        "   • Remove unwanted links\n"
        "   • Format caption exactly like Shitij Style 🔥\n\n"
        "✅ Works automatically for videos and documents."
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


@bot.message_handler(commands=['whereadmin'])
def where_admin(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only.")
        return
    if not TARGET_CHATS:
        bot.reply_to(msg, "🤖 Bot is not admin in any group/channel yet.")
        return
    text = "📋 <b>ISH Bot is admin in:</b>\n\n"
    for chat_id in TARGET_CHATS:
        text += f"🔹 <code>{chat_id}</code>\n"
    bot.reply_to(msg, text)


@bot.message_handler(commands=['removechat'])
def remove_chat(msg):
    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ Admin only.")
        return
    try:
        parts = msg.text.split()
        if len(parts) < 2:
            bot.reply_to(msg, "Usage: /removechat <chat_id>")
            return
        chat_id = int(parts[1])
        if chat_id in TARGET_CHATS:
            TARGET_CHATS.remove(chat_id)
            bot.reply_to(msg, f"✅ Removed chat: <code>{chat_id}</code>")
        else:
            bot.reply_to(msg, "⚠️ Chat ID not found.")
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

    # Clean caption
    new_caption = clean_filename(original_name)

    try:
        # Send cleaned version to sender
        send_func(msg.chat.id, file_id, caption=new_caption, parse_mode="HTML", **extra_args)

        # Forward to target chats
        for target in TARGET_CHATS:
            try:
                send_func(target, file_id, caption=new_caption, parse_mode="HTML", **extra_args)
            except Exception as e:
                print(f"⚠️ Failed to send to {target}: {e}")

        # Send to dump channel
        try:
            send_func(DUMP_CHANNEL_ID, file_id, caption=new_caption, parse_mode="HTML", **extra_args)
        except Exception as e:
            print(f"⚠️ Failed to send to dump channel: {e}")

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error sending: {e}")


# --- Track where bot is admin ---
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
print("🤖 ISH Bot (Shitij Edition) running — auto Shitij/@ShitijRips cleaner, caption formatter, and dump sender!")

bot.remove_webhook()
bot.infinity_polling(skip_pending=True, timeout=20)
