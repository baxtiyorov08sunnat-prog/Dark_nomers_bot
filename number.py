import asyncio
import sqlite3
from datetime import datetime
from aiogram import Bot, Dispatcher, types
from aiogram.types import ReplyKeyboardMarkup, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

TOKEN = "8305324899:AAHGndr3MMh8-7snEYIo_q_MoB3M20UaBEE"
ADMIN_ID = 7696027042
SALES_CHANNEL = "@dark_nomer_channel"   # masalan: "@nomer_sotuvlari"

# Narxlar
PRICES = {
    "BD": 10000,
    "VN": 9000,
    "UZ": 15000
}

COUNTRY_NAMES = {
    "BD": "Bangladesh",
    "VN": "Vietnam",
    "UZ": "Uzbekistan"
}

# Foydalanuvchi vaqtincha summa saqlash (FSM o‘rniga)
user_amount = {}

# ------------------ DATABASE ------------------
conn = sqlite3.connect("database.db")
cur = conn.cursor()

cur.execute("""
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE,
    balance INTEGER DEFAULT 0
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS numbers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    number TEXT,
    country TEXT,
    price INTEGER,
    status TEXT DEFAULT 'free',
    code TEXT
)
""")

cur.execute("""
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER,
    amount INTEGER,
    file_id TEXT,
    status TEXT DEFAULT 'pending'
)
""")

conn.commit()

# ------------------ BOT ------------------
bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# ------------------ KEYBOARDS ------------------
main_menu = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu.add("📱 Nomer olish")
main_menu.add("👤 Kabinet")
main_menu.add("💵 Pul kiritish")

countries_kb = InlineKeyboardMarkup()
countries_kb.add(
    InlineKeyboardButton("🇧🇩 Bangladesh", callback_data="country_BD"),
    InlineKeyboardButton("🇻🇳 Vietnam", callback_data="country_VN"),
    InlineKeyboardButton("🇺🇿 Uzbekistan", callback_data="country_UZ")
)

# ------------------ HELPERS ------------------
def get_user(tg_id):
    cur.execute("SELECT * FROM users WHERE telegram_id=?", (tg_id,))
    return cur.fetchone()

def create_user(tg_id):
    cur.execute("INSERT INTO users (telegram_id) VALUES (?)", (tg_id,))
    conn.commit()
    return get_user(tg_id)

def get_free_number(country):
    cur.execute("SELECT * FROM numbers WHERE country=? AND status='free' LIMIT 1", (country,))
    return cur.fetchone()

def set_number_sold(num_id):
    cur.execute("UPDATE numbers SET status='sold' WHERE id=?", (num_id,))
    conn.commit()

def set_number_finished(num_id):
    cur.execute("UPDATE numbers SET status='finished' WHERE id=?", (num_id,))
    conn.commit()

# ------------------ /START ------------------
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user = get_user(message.from_user.id)
    if not user:
        user = create_user(message.from_user.id)

    await message.answer(
        f"Assalomu alaykum!\n"
        f"Sizning ID: {user[0]}\n"
        f"Botdan foydalanishingiz mumkin.",
        reply_markup=main_menu
    )

# ------------------ KABINET ------------------
@dp.message_handler(lambda m: m.text == "👤 Kabinet")
async def cabinet(message: types.Message):
    user = get_user(message.from_user.id)
    await message.answer(
        f"📊 Hisobingiz:\n"
        f"💳 Balans: {user[2]} so'm\n"
        f"🆔 ID: {user[0]}"
    )

# ------------------ PUL KIRITISH ------------------
@dp.message_handler(lambda m: m.text == "💵 Pul kiritish")
async def add_balance(message: types.Message):
    await message.answer("💰 Summani yuboring (masalan: 10000):")

@dp.message_handler(lambda m: m.text.isdigit())
async def get_amount(message: types.Message):
    amount = int(message.text)
    if amount < 1000:
        await message.answer("❌ Minimal summa: 1000 so'm")
        return

    user_amount[message.from_user.id] = amount
    await message.answer("📎 Endi to‘lov chekini (rasm) yuboring.")

@dp.message_handler(content_types=types.ContentType.PHOTO)
async def get_receipt(message: types.Message):
    amount = user_amount.get(message.from_user.id)
    if not amount:
        await message.answer("❌ Avval summani kiriting.")
        return
    user = get_user(message.from_user.id)
    cur.execute(
        "INSERT INTO payments (user_id, amount, file_id) VALUES (?, ?, ?)",
        (user[0], amount, message.photo[-1].file_id)
    )
    conn.commit()

    pay_id = cur.lastrowid

    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"pay_ok_{pay_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"pay_no_{pay_id}")
    )

    await bot.send_photo(
        ADMIN_ID,
        message.photo[-1].file_id,
        caption=f"💵 To‘lov:\nUser ID: {user[0]}\nSumma: {amount}",
        reply_markup=kb
    )

    await message.answer("⏳ Chekingiz adminga yuborildi. Tekshirilmoqda...")

# ------------------ ADMIN TASDIQLASH ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("pay_"))
async def payment_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        return

    _, action, pay_id = call.data.split("_")

    cur.execute("SELECT * FROM payments WHERE id=?", (pay_id,))
    pay = cur.fetchone()
    if not pay:
        await call.answer("Topilmadi")
        return

    user_id = pay[1]
    amount = pay[2]

    if action == "ok":
        cur.execute("UPDATE users SET balance = balance + ? WHERE id=?", (amount, user_id))
        cur.execute("UPDATE payments SET status='approved' WHERE id=?", (pay_id,))
        conn.commit()
        await call.message.edit_caption("✅ To‘lov tasdiqlandi")
    else:
        cur.execute("UPDATE payments SET status='rejected' WHERE id=?", (pay_id,))
        conn.commit()
        await call.message.edit_caption("❌ To‘lov rad etildi")

# ------------------ NOMER OLISH ------------------
@dp.message_handler(lambda m: m.text == "📱 Nomer olish")
async def get_number(message: types.Message):
    await message.answer("🌍 Davlatni tanlang:", reply_markup=countries_kb)

@dp.callback_query_handler(lambda c: c.data.startswith("country_"))
async def choose_country(call: types.CallbackQuery):
    country = call.data.split("_")[1]
    price = PRICES[country]

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ SOTIB OLISH", callback_data=f"buy_{country}"))

    await call.message.edit_text(
        f"🎯 {COUNTRY_NAMES[country]}\n💰 Narx: {price} so'm",
        reply_markup=kb
    )

# ------------------ SOTIB OLISH (KANALGA XABAR BILAN) ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("buy_"))
async def buy_number(call: types.CallbackQuery):
    country = call.data.split("_")[1]
    price = PRICES[country]
    user = get_user(call.from_user.id)

    if user[2] < price:
        await call.answer("❌ Balansingiz yetarli emas", show_alert=True)
        return

    number = get_free_number(country)
    if not number:
        await call.answer("❌ Bu davlat uchun raqam qolmadi", show_alert=True)
        return

    cur.execute("UPDATE users SET balance = balance - ? WHERE id=?", (price, user[0]))
    set_number_sold(number[0])
    conn.commit()

    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔐 CODNI OLISH", callback_data=f"code_{number[0]}"))

    await call.message.edit_text(
        f"📱 Sizning akkauntingiz:\n{number[1]}\n\n⏳ Kod kelishini kuting",
        reply_markup=kb
    )

    username = f"@{call.from_user.username}" if call.from_user.username else f"ID {call.from_user.id}"
    now = datetime.now().strftime("%d.%m.%Y %H:%M")

    await bot.send_message(
        SALES_CHANNEL,
        "📱 *Yangi sotuv!*\n\n"
        f"👤 Foydalanuvchi: {username}\n"
        f"🆔 Ichki ID: {user[0]}\n"
        f"🌍 Davlat: {COUNTRY_NAMES[country]}\n"
        f"📞 Raqam: {number[1]}\n"
        f"💰 Narx: {price} so'm\n"
        f"⏰ Sana: {now}",
        parse_mode="Markdown"
    )

# ------------------ CODNI OLISH ------------------
@dp.callback_query_handler(lambda c: c.data.startswith("code_"))
async def get_code(call: types.CallbackQuery):
    num_id = call.data.split("_")[1]
    cur.execute("SELECT * FROM numbers WHERE id=?", (num_id,))
    num = cur.fetchone()
    if not num or not num[5]:
        await call.answer("⏳ Kod hali kelmadi", show_alert=True)
        return

    await call.message.edit_text(
        f"✅ Kod: {num[5]}\n\n🔓 Endi akkauntga kirishingiz mumkin"
    )
    set_number_finished(num_id)

# ------------------ RUN ------------------

executor.start_polling(dp, skip_updates=True)
