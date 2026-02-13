import telebot
import re
import html
import time
from threading import Thread

# ---------------- CONFIG ---------------- #

BOT_TOKEN = "8338489595:AAFM9H8I9FYtJw7j-VZgVFHE3wPHykX4CQ4"
bot = telebot.TeleBot(BOT_TOKEN, parse_mode="HTML")

BRAND = "@ShitijRips"

ADMINS = set()
TARGET_CHATS = set()

DUMP_CHANNEL_ID = -1002990446200
TELEGRAM_CAPTION_LIMIT = 1024

media_queue = []


# ---------------- CLEAN FUNCTION ---------------- #

def clean_caption(original: str) -> str:
    if not original:
        original = "Video.mp4"

    text = re.sub(r"https?://(?!t\.me)\S+", "", original)
    text = re.sub(r"@\w+", BRAND, text)

    lines = [l.strip() for l in text.splitlines() if l.strip()]
    filename = lines[0]

    filename = re.sub(r"[\s/]+", ".", filename).strip(" .")

    if not filename.lower().endswith((".mp4", ".mkv", ".avi")):
        filename += ".mp4"

    caption = (
        f"<code>{html.escape(filename)}</code>\n\n"
        f"💝Join Our Main Channel : {BRAND}💥"
    )

    return caption[:TELEGRAM_CAPTION_LIMIT]


# ---------------- ADD ADMIN (ANYONE) ---------------- #

@bot.message_handler(commands=["addadminsme"])
def add_self_admin(msg):
    ADMINS.add(msg.from_user.id)
    bot.delete_message(msg.chat.id, msg.message_id)


# ---------------- PROCESS QUEUE (20-20 MEDIA GROUP) ---------------- #

def process_queue():
    while media_queue:
        batch = media_queue[:20]
        del media_queue[:20]

        for chat in list(TARGET_CHATS) + [DUMP_CHANNEL_ID]:
            try:
                media_group = []
                for item in batch:
                    file_id, caption = item
                    media = telebot.types.InputMediaVideo(
                        media=file_id,
                        caption=caption if batch.index(item) == 0 else ""
                    )
                    media_group.append(media)

                bot.send_media_group(chat, media_group)
                time.sleep(2)

            except:
                pass


# ---------------- MEDIA HANDLER ---------------- #

@bot.message_handler(content_types=["video"])
def handle_video(msg):

    if msg.from_user.id not in ADMINS:
        bot.reply_to(msg, "❌ Use /addadminsme First")
        return

    src = msg.caption or msg.video.file_name
    caption = clean_caption(src)

    media_queue.append((msg.video.file_id, caption))

    if len(media_queue) == 1:
        Thread(target=process_queue).start()


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

print("🤖 20x20 Turbo Batch Bot Running")
bot.infinity_polling(skip_pending=True)
