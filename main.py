import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters
)

# ========= CONFIG =========
TOKEN = "BOT_TOKENINGNI_BU_YERGA_QO‘Y"
ADMIN_ID = 7696027042
LOG_CHANNEL_ID = -1001234567890  # agar log kanal bo‘lsa, yo‘q bo‘lsa o‘chir

logging.basicConfig(level=logging.INFO)

# ========= DATABASE =========
db = sqlite3.connect("database.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0,
    step TEXT DEFAULT 'menu'
)
""")
db.commit()

# ========= DATA =========
NUMBERS = {
    "Bangladesh": {"price": 10000, "numbers": ["+880123456789"]},
    "Vietnam": {"price": 9000, "numbers": ["+84987654321"]},
}

CARD_INFO = (
    "💳 Karta: 8600 1234 5678 9012\n"
    "👤 Egasi: Baxtiyorov B.\n"
    "📞 Tel: +99890XXXXXXX"
)

# ========= START =========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    sql.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (user_id,))
    sql.execute("UPDATE users SET step='menu' WHERE user_id=?", (user_id,))
    db.commit()

    keyboard = [
        [InlineKeyboardButton("📱 Nomer olish", callback_data="buy")],
        [InlineKeyboardButton("💳 To‘lov qilish", callback_data="pay")],
        [InlineKeyboardButton("👤 Kabinet", callback_data="cabinet")]
    ]

    await update.message.reply_text(
        "🖤 Dark Nomer Bot\n\nBo‘limni tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= BUY =========
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    keyboard = [
        [InlineKeyboardButton(c, callback_data=f"country_{c}")]
        for c in NUMBERS
    ]
    keyboard.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="menu")])

    await q.edit_message_text(
        "🌍 Davlat tanlang:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# ========= COUNTRY =========
async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    country = q.data.replace("country_", "")
    context.user_data["country"] = country

    price = NUMBERS[country]["price"]

    await q.edit_message_text(
        f"📍 {country}\n💰 Narx: {price} so‘m\n\nBalansingiz yetarli bo‘lsa sotib olinadi."
    )

# ========= PAYMENT =========
async def payment(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    sql.execute("UPDATE users SET step='wait_amount' WHERE user_id=?", (q.from_user.id,))
    db.commit()

    await q.edit_message_text("💰 Summani kiriting:")

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id
    text = update.message.text

    sql.execute("SELECT step FROM users WHERE user_id=?", (user_id,))
    step = sql.fetchone()[0]

    if step != "wait_amount":
        return

    if not text.isdigit():
        await update.message.reply_text("❌ Faqat raqam kiriting")
        return

    amount = int(text)
    context.user_data["amount"] = amount

    sql.execute("UPDATE users SET step='wait_check' WHERE user_id=?", (user_id,))
    db.commit()

    await update.message.reply_text(CARD_INFO + "\n\n📸 Chekni yuboring")

async def get_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.message.from_user.id

    sql.execute("SELECT step FROM users WHERE user_id=?", (user_id,))
    step = sql.fetchone()[0]

    if step != "wait_check":
        return

    amount = context.user_data.get("amount")
    await context.bot.send_photo(
        ADMIN_ID,
        update.message.photo[-1].file_id,
        caption=f"🧾 Yangi to‘lov\n👤 {user_id}\n💰 {amount}",
        reply_markup=InlineKeyboardMarkup([
            [
                InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{user_id}_{amount}"),
                InlineKeyboardButton("❌ Rad etish", callback_data=f"no_{user_id}")
            ]
        ])
    )

    sql.execute("UPDATE users SET step='menu' WHERE user_id=?", (user_id,))
    db.commit()

    await update.message.reply_text("⏳ Kutilmoqda. Admin tekshiryapti.")

# ========= ADMIN =========
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = q.data.split("_")

    if data[0] == "ok":
        user_id = int(data[1])
        amount = int(data[2])

        sql.execute("UPDATE users SET balance = balance + ? WHERE user_id=?", (amount, user_id))
        db.commit()

        await context.bot.send_message(user_id, "✅ To‘lov tasdiqlandi")
    else:
        user_id = int(data[1])
        await context.bot.send_message(user_id, "❌ To‘lov rad etildi")

# ========= ROUTER =========
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    data = update.callback_query.data

    if data == "buy":
        await buy(update, context)
    elif data == "pay":
        await payment(update, context)
    elif data == "menu":
        await start(update, context)
    elif data.startswith("country_"):
        await select_country(update, context)
    elif data.startswith("ok_") or data.startswith("no_"):
        await admin_action(update, context)

# ========= MAIN =========
def main():
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(router))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount))
    app.add_handler(MessageHandler(filters.PHOTO, get_check))

    print("🖤 Dark Nomer Bot ishga tushdi")
    app.run_polling(drop_pending_updates=True)

if __name__ == "__main__":
    main()
