import os
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes

from number import take_number   # 👈 number.py dan funksiya chaqiryapmiz

TOKEN = os.getenv("BOT_TOKEN")

# ------------------ COMMANDS ------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["Bangladesh", "Vietnam"],
        ["Uzbekistan"]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)

    await update.message.reply_text(
        "📲 *Dark Nomers Bot*\n\n"
        "Davlatni tanlang va tizim sizga avtomatik nomer beradi:",
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )

async def get_number(update: Update, context: ContextTypes.DEFAULT_TYPE):
    country = update.message.text.strip()

    if country not in ["Bangladesh", "Vietnam", "Uzbekistan"]:
        await update.message.reply_text("❌ Iltimos, menyudan davlat tanlang.")
        return

    number = take_number(country)   # 👈 number.py ichidagi funksiya

    if not number:
        await update.message.reply_text(f"❌ {country} uchun nomer tugadi.")
        return

    await update.message.reply_text(
        f"✅ *Sizning nomeringiz:*\n\n📞 {number}\n\n"
        "🔐 Endi Telegram kod shu nomerga keladi.",
        parse_mode="Markdown"
    )

# ------------------ MAIN ------------------

def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_number))

    print("🤖 Dark Nomers Bot ishga tushdi...")
    app.run_polling()

if name == "main":
    main()
