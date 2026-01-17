import json
import sqlite3
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    ApplicationBuilder, CommandHandler,
    CallbackQueryHandler, MessageHandler,
    ContextTypes, filters
)

# ================= CONFIG =================
TOKEN = "8305324899:AAHGndr3MMh8-7snEYIo_q_MoB3M20UaBEE"
ADMIN_ID = 7696027042
LOG_CHANNEL = -1003674226792   # kanal ID (minus bilan)

CARD_TEXT = (
    "💳 Karta: 9860 1666 5369 5071\n"
    "👤 Egasi: RIZAYEV JAVOXIR.\n"
    "📞 Tel: +998882883031"
)

logging.basicConfig(level=logging.INFO)

# ================= DATABASE =================
db = sqlite3.connect("database.db", check_same_thread=False)
sql = db.cursor()

sql.execute("""
CREATE TABLE IF NOT EXISTS users(
    user_id INTEGER PRIMARY KEY,
    balance INTEGER DEFAULT 0
)
""")

sql.execute("""
CREATE TABLE IF NOT EXISTS payments(
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    status TEXT
)
""")
db.commit()

# ================= LOAD NUMBERS =================
def load_numbers():
    with open("numbers.json", "r", encoding="utf-8") as f:
        return json.load(f)

# ================= START =================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id
    sql.execute("INSERT OR IGNORE INTO users(user_id) VALUES(?)", (uid,))
    db.commit()

    kb = [
        [InlineKeyboardButton("📱 Nomer olish", callback_data="buy")],
        [InlineKeyboardButton("💳 To‘lov qilish", callback_data="pay")],
        [InlineKeyboardButton("👤 Kabinet", callback_data="cabinet")]
    ]
    await update.message.reply_text(
        "🖤 Dark Nomer Bot",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# ================= KABINET =================
async def cabinet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    sql.execute("SELECT balance FROM users WHERE user_id=?", (q.from_user.id,))
    bal = sql.fetchone()[0]

    await q.edit_message_text(f"👤 ID: {q.from_user.id}\n💰 Balans: {bal} so‘m")

# ================= BUY =================
async def buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    data = load_numbers()
    kb = [[InlineKeyboardButton(c, callback_data=f"c_{c}")] for c in data]
    kb.append([InlineKeyboardButton("⬅️ Orqaga", callback_data="menu")])

    await q.edit_message_text("🌍 Davlatni tanlang:", reply_markup=InlineKeyboardMarkup(kb))

async def select_country(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    country = q.data[2:]
    data = load_numbers()

    if not data[country]["numbers"]:
        await q.edit_message_text("❌ Bu davlatda nomer yo‘q")
        return

    price = data[country]["price"]
    context.user_data["country"] = country

    kb = [[InlineKeyboardButton("✅ Sotib olish", callback_data="confirm_buy")]]
    await q.edit_message_text(
        f"📍 {country}\n💰 Narx: {price} so‘m",
        reply_markup=InlineKeyboardMarkup(kb)
    )

async def confirm_buy(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    country = context.user_data["country"]
    data = load_numbers()
    price = data[country]["price"]

    sql.execute("SELECT balance FROM users WHERE user_id=?", (q.from_user.id,))
    bal = sql.fetchone()[0]

    if bal < price:
        await q.edit_message_text("❌ Balans yetarli emas")
        return

    number = data[country]["numbers"].pop(0)

    sql.execute("UPDATE users SET balance=balance-? WHERE user_id=?", (price, q.from_user.id))
    db.commit()

    with open("numbers.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    await q.edit_message_text(f"✅ Nomer: {number}")

    await context.bot.send_message(
        LOG_CHANNEL,
        f"📤 SOTILDI\n👤 {q.from_user.id}\n📍 {country}\n📞 {number}\n💰 {price}"
    )
    # ================= PAYMENT =================
async def pay(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()
    await q.edit_message_text("💰 Summani yozing:")

async def get_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message.text.isdigit():
        return

    amount = int(update.message.text)
    context.user_data["amount"] = amount

    await update.message.reply_text(CARD_TEXT + "\n\n📸 Chek yuboring")

async def get_check(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.message.from_user.id
    amount = context.user_data["amount"]

    sql.execute("INSERT INTO payments(user_id,amount,status) VALUES(?,?,?)",
                (uid, amount, "wait"))
    db.commit()

    kb = [[
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"ok_{uid}_{amount}"),
        InlineKeyboardButton("❌ Rad", callback_data=f"no_{uid}")
    ]]

    await context.bot.send_message(
        ADMIN_ID,
        f"🧾 To‘lov\n👤 {uid}\n💰 {amount}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

    await update.message.reply_text("⏳ Kutilmoqda...")

# ================= ADMIN =================
async def admin_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    d = q.data.split("_")
    uid = int(d[1])

    if d[0] == "ok":
        amount = int(d[2])
        sql.execute("UPDATE users SET balance=balance+? WHERE user_id=?", (amount, uid))
        db.commit()

        await context.bot.send_message(uid, "✅ To‘lov tasdiqlandi")
        await q.edit_message_text("Tasdiqlandi")
    else:
        await context.bot.send_message(uid, "❌ To‘lov rad etildi")
        await q.edit_message_text("Rad etildi")

# ================= ROUTER =================
async def router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    d = update.callback_query.data

    if d == "buy":
        await buy(update, context)
    elif d == "pay":
        await pay(update, context)
    elif d == "cabinet":
        await cabinet(update, context)
    elif d == "menu":
        await start(update, context)
    elif d.startswith("c_"):
        await select_country(update, context)
    elif d == "confirm_buy":
        await confirm_buy(update, context)
    elif d.startswith("ok_") or d.startswith("no_"):
        await admin_action(update, context)

# ================= RUN =================
app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(router))
app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, get_amount))
app.add_handler(MessageHandler(filters.PHOTO, get_check))

print("🖤 Dark Nomer Bot ishga tushdi")
app.run_polling()
