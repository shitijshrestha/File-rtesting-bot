import telebot
import re
import html

# ---------------- CONFIG ----------------
BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

ADMINS = set()
TARGET_CHATS = set()
DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024

# ---------------- HELPERS ----------------
def clean_filename_and_caption(original: str) -> (str, str):
    """
    Clean filename:
    - Remove any trailing creator tags
    - Replace DG_Contents/tvshowhub/etc.
    - Add _ShitijRips.mp4 suffix
    - Caption is always: Join:-[@ShitijRips]
    """
    if not original:
        original = "Video.mp4"

    # Remove normal links
    no_links = re.sub(r"(https?://\S+)", "", original)

    # Remove any trailing creator tags like -Mrn_Officialx, -SRBRips, -DG_Contents
    no_extra_tags = re.sub(r"-[@\w]+$", "", no_links)

    # Replace DG_Contents, tvshowhub, etc. with Shitij
    replaced = re.sub(
        r"(?i)(DG_Contents|tvshowhub|tvshow|hub|bhavik611|mrxvoltz|srp_main_channel|srbrips)",
        "Shitij",
        no_extra_tags,
    )

    # Collapse multiple "Shitij"
    replaced = re.sub(r"(Shitij)+", "Shitij", replaced)

    # Replace spaces/slashes with dots
    cleaned_name = re.sub(r"[\s/]+", ".", replaced).strip(" .")

    # Add _ShitijRips.mp4 suffix
    cleaned_name = re.sub(r"\.mp4$", "", cleaned_name, flags=re.IGNORECASE)
    cleaned_name += "_ShitijRips.mp4"

    # Caption line
    caption = f"Join:-[@ShitijRips]"

    return cleaned_name, caption

# ---------------- COMMANDS ----------------
@bot.message_handler(commands=['start'])
def start(msg):
    bot.reply_to(
        msg,
        "👋 Welcome!\n\n"
        "📌 Send any video/document, I'll:\n"
        "   - Clean filename\n"
        "   - Remove extra creator tags\n"
        "   - Add _ShitijRips.mp4 suffix\n"
        "   - Add caption: Join:-[@ShitijRips]\n"
        "✅ Forward/send exactly this format."
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

# ---------------- MEDIA HANDLER ----------------
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

    cleaned_name, caption = clean_filename_and_caption(original_name)

    try:
        # Send back to sender
        send_func(msg.chat.id, file_id, caption=f"{cleaned_name}\n{caption}", parse_mode="HTML", **extra_args)

        # Forward to admin targets
        for target in TARGET_CHATS:
            try:
                send_func(target, file_id, caption=f"{cleaned_name}\n{caption}", parse_mode="HTML", **extra_args)
            except Exception as e:
                print(f"⚠️ Failed to send to {target}: {e}")

        # Send to dump channel
        try:
            send_func(DUMP_CHANNEL_ID, file_id, caption=f"{cleaned_name}\n{caption}", parse_mode="HTML", **extra_args)
        except Exception as e:
            print(f"⚠️ Failed to send to dump channel: {e}")

    except Exception as e:
        bot.reply_to(msg, f"⚠️ Error sending: {e}")

# ---------------- TRACK BOT ADMIN STATUS ----------------
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

# ---------------- RUN BOT ----------------
print("🤖 ISH Bot running: sending all files with _ShitijRips suffix and Join:-[@ShitijRips] caption...")
bot.remove_webhook()
bot.infinity_polling(skip_pending=True, timeout=20)
