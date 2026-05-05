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

authorized_users = set()
user_links = {}
pending_codes = {}

os.makedirs("downloads", exist_ok=True)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [[InlineKeyboardButton("🔐 طلب كود دخول", callback_data="request_code")]]
    await update.message.reply_text(
        "أهلاً 👋\nلازم تطلب كود دخول من صاحب البوت.",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id
    username = query.from_user.username or "بدون يوزر"
    name = query.from_user.full_name

    if query.data == "request_code":
        code = str(random.randint(100000, 999999))

        pending_codes[user_id] = {
            "code": code,
            "expires": time.time() + CODE_EXPIRE_SECONDS
        }

        await context.bot.send_message(
            chat_id=OWNER_ID,
            text=f"🔐 طلب كود جديد\n\nالاسم: {name}\nاليوزر: @{username}\nID: {user_id}\n\nالكود: {code}\nصالح 12 ساعة"
        )

        await query.edit_message_text("تم طلب الكود ✅\nخذ الكود من صاحب البوت واكتبه هنا.")
        return

    await download_file(update, context)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    if user_id not in authorized_users:
        data = pending_codes.get(user_id)

        if not data:
            await update.message.reply_text("اضغط /start ثم اطلب كود دخول 🔐")
            return

        if time.time() > data["expires"]:
            pending_codes.pop(user_id, None)
            await update.message.reply_text("الكود انتهى ❌\nاطلب كود جديد من /start")
            return

        if text == data["code"]:
            authorized_users.add(user_id)
            pending_codes.pop(user_id, None)

            try:
                await update.message.delete()
            except:
                pass

            await update.message.reply_text("تم تفعيل البوت لك ✅\nارسل رابط الآن.")
            return
        else:
            await update.message.reply_text("الكود غلط ❌")
            return

    if not text.startswith("http"):
        await update.message.reply_text("ارسل رابط صحيح يبدأ بـ http")
        return

    user_links[user_id] = text

    keyboard = [
        [InlineKeyboardButton("🎥 فيديو", callback_data="video")],
        [InlineKeyboardButton("🎵 صوت", callback_data="audio")]
    ]

    await update.message.reply_text(
        "اختر نوع التحميل:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def download_file(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if user_id not in authorized_users:
        await query.edit_message_text("اطلب كود دخول أول 🔐")
        return

    url = user_links.get(user_id)

    if not url:
        await query.edit_message_text("ارسل الرابط أول.")
        return

    await query.edit_message_text("جاري التحميل... ⏳")

    try:
        if query.data == "video":
            ydl_opts = {
                "format": "best",
                "outtmpl": "downloads/%(id)s.%(ext)s"
            }
        else:
            ydl_opts = {
                "format": "bestaudio/best",
                "outtmpl": "downloads/%(id)s.%(ext)s"
            }

        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            file_name = ydl.prepare_filename(info)

        await query.edit_message_text("جاري الإرسال... 📤")

        with open(file_name, "rb") as f:
            await context.bot.send_document(
                chat_id=query.message.chat_id,
                document=f
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


app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
app.add_handler(CallbackQueryHandler(button))

print("BOT RUNNING")
app.run_polling()