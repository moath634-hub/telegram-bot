import os
import random
import time
import yt_dlp

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters
)

TOKEN = "8671260107:AAEiDgZwAA6mdNLVZY8bED1gh-x7hY2w1Tg"
OWNER_ID = 1590614988

CODE_EXPIRE_SECONDS = 43200  # 12 ساعة

authorized_users = {}
user_links = {}
pending_codes = {}

os.makedirs("downloads", exist_ok=True)


def is_authorized(user_id):

    if user_id not in authorized_users:
        return False

    if time.time() > authorized_users[user_id]:
        authorized_users.pop(user_id, None)
        return False

    return True


async def start(update: Update,
                context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [
            InlineKeyboardButton(
                "🔐 طلب كود دخول",
                callback_data="request_code"
            )
        ]
    ]

    await update.message.reply_text(
        "أهلاً 👋\nلازم تطلب كود دخول من صاحب البوت.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update,
                 context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "بدون يوزر"
    name = query.from_user.full_name

    # =========================
    # طلب كود
    # =========================

    if query.data == "request_code":

        code = str(random.randint(100000, 999999))

        pending_codes[user_id] = {
            "code": code,
            "expires": time.time() + CODE_EXPIRE_SECONDS
        }

        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=
            f"🔐 طلب كود جديد\n\n"
            f"الاسم: {name}\n"
            f"اليوزر: @{username}\n"
            f"ID: {user_id}\n\n"
            f"الكود: {code}\n"
            f"صالح 12 ساعة"
        )

        await query.edit_message_text(
            "تم طلب الكود ✅\n"
            "خذ الكود من صاحب البوت واكتبه هنا."
        )

        return

    await download_file(update, context)


async def handle_message(update: Update,
                         context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    text = update.message.text.strip()

    # =========================
    # تحقق التفعيل
    # =========================

    if not is_authorized(user_id):

        data = pending_codes.get(user_id)

        if not data:

            await update.message.reply_text(
                "اضغط /start ثم اطلب كود دخول 🔐"
            )

            return

        if time.time() > data["expires"]:

            pending_codes.pop(user_id, None)

            await update.message.reply_text(
                "الكود انتهى ❌\n"
                "اطلب كود جديد من /start"
            )

            return

        if text == data["code"]:

            authorized_users[user_id] = (
                time.time() + CODE_EXPIRE_SECONDS
            )

            pending_codes.pop(user_id, None)

            try:
                await update.message.delete()
            except:
                pass

            await update.message.reply_text(
                "تم التفعيل لمدة 12 ساعة ✅\n"
                "ارسل رابط الآن."
            )

            return

        else:

            await update.message.reply_text(
                "الكود غلط ❌"
            )

            return

    # =========================
    # تحقق الرابط
    # =========================

    if not text.startswith("http"):

        await update.message.reply_text(
            "ارسل رابط صحيح يبدأ بـ http"
        )

        return

    user_links[user_id] = text

    keyboard = [

        [
            InlineKeyboardButton(
                "🎵 صوت MP3",
                callback_data="audio"
            )
        ],

        [
            InlineKeyboardButton(
                "🎥 فيديو 360p",
                callback_data="video_360"
            )
        ],

        [
            InlineKeyboardButton(
                "🎬 فيديو 720p",
                callback_data="video_720"
            )
        ],

        [
            InlineKeyboardButton(
                "🚀 أفضل جودة",
                callback_data="video_best"
            )
        ]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def download_file(update: Update,
                        context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if not is_authorized(user_id):

        await query.edit_message_text(
            "انتهت صلاحيتك ❌\n"
            "اطلب كود جديد من /start"
        )

        return

    url = user_links.get(user_id)

    if not url:

        await query.edit_message_text(
            "ارسل الرابط أول."
        )

        return

    await query.edit_message_text(
        "جاري التحميل... ⏳"
    )

    try:

        # =========================
        # MP3
        # =========================

        if query.data == "audio":

            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s",
                "postprocessors": [{
                    "key": "FFmpegExtractAudio",
                    "preferredcodec": "mp3",
                    "preferredquality": "192",
                }]
            }

        # =========================
        # 360p
        # =========================

        elif query.data == "video_360":

            ydl_opts = {
                "format": "bestvideo[height<=360]+bestaudio/best[height<=360]",
                "merge_output_format": "mp4",
                "outtmpl": "downloads/%(id)s.%(ext)s"
            }

        # =========================
        # 720p
        # =========================

        elif query.data == "video_720":

            ydl_opts = {
                "format": "bestvideo[height<=720]+bestaudio/best[height<=720]",
                "merge_output_format": "mp4",
                "outtmpl": "downloads/%(id)s.%(ext)s"
            }

        # =========================
        # أفضل جودة
        # =========================

        else:

            ydl_opts = {
                "format": "bestvideo+bestaudio/best",
                "merge_output_format": "mp4",
                "outtmpl": "downloads/%(id)s.%(ext)s"
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:

            info = ydl.extract_info(
                url,
                download=True
            )

            file_name = ydl.prepare_filename(info)

            if query.data == "audio":

                file_name = (
                    os.path.splitext(file_name)[0]
                    + ".mp3"
                )

        # =========================
        # تحقق حجم الملف
        # =========================

        file_size = os.path.getsize(file_name)

        max_size = 49 * 1024 * 1024

        if file_size > max_size:

            os.remove(file_name)

            await context.bot.send_message(
                chat_id=query.message.chat_id,
                text=
                "الفيديو كبير جدًا ❌\n"
                "اختر جودة أقل."
            )

            return

        await query.edit_message_text(
            "جاري الإرسال... 📤"
        )

        with open(file_name, "rb") as f:

            if query.data == "audio":

                await context.bot.send_audio(
                    chat_id=query.message.chat_id,
                    audio=f,
                    read_timeout=300,
                    write_timeout=300
                )

            else:

                await context.bot.send_video(
                    chat_id=query.message.chat_id,
                    video=f,
                    read_timeout=300,
                    write_timeout=300
                )

        os.remove(file_name)

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text="تم ✅"
        )

    except Exception as e:

        await context.bot.send_message(
            chat_id=query.message.chat_id,
            text=f"صار خطأ ❌\n{e}"
        )


# =========================
# تشغيل البوت
# =========================

app = (
    ApplicationBuilder()
    .token(TOKEN)
    .connect_timeout(60)
    .read_timeout(300)
    .write_timeout(300)
    .pool_timeout(300)
    .build()
)

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        handle_message
    )
)

app.add_handler(
    CallbackQueryHandler(button)
)

print("BOT RUNNING")

try:
    app.run_polling()
except Exception as e:
    print("ERROR:")
    print(e)
    input("اضغط Enter للخروج...")