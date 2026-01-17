import os
import logging
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import (
    ReplyKeyboardMarkup, KeyboardButton,
    InlineKeyboardMarkup, InlineKeyboardButton
)

from number import take_number  # 👈 number.py dan chaqiramiz

# ===== SOZLAMALAR =====
BOT_TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 7696027042

logging.basicConfig(level=logging.INFO)

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


# ===== STATES =====
class PaymentState(StatesGroup):
    waiting_sum = State()
    waiting_check = State()


# ===== KEYBOARDS =====
def main_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("📦 Nomer olish"),
        KeyboardButton("💼 Kabinet"),
        KeyboardButton("💳 To‘lov qilish")
    )
    return kb


def country_menu():
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(
        KeyboardButton("🇧🇩 Bangladesh"),
        KeyboardButton("🇻🇳 Vietnam"),
        KeyboardButton("🇺🇿 Uzbekistan"),
        KeyboardButton("⬅️ Orqaga")
    )
    return kb


def admin_payment_kb(user_id: int):
    kb = InlineKeyboardMarkup()
    kb.add(
        InlineKeyboardButton("✅ Tasdiqlash", callback_data=f"pay_ok:{user_id}"),
        InlineKeyboardButton("❌ Rad etish", callback_data=f"pay_no:{user_id}")
    )
    return kb


# ===== /START =====
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(
        "🕶 *Dark Nomer Bot*\n\nKerakli bo‘limni tanlang:",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ===== NOMER OLISH =====
@dp.message_handler(text="📦 Nomer olish")
async def nomer_olish(message: types.Message):
    await message.answer("🌍 Davlatni tanlang:", reply_markup=country_menu())


@dp.message_handler(lambda m: m.text in ["🇧🇩 Bangladesh", "🇻🇳 Vietnam", "🇺🇿 Uzbekistan"])
async def send_number(message: types.Message):
    country = message.text.split()[-1]
    number = take_number(country)

    if not number:
        await message.answer("❌ Bu davlat uchun nomer qolmagan", reply_markup=main_menu())
        return

    await message.answer(
        f"📱 *Sizning nomeringiz:*\n{number}\n\n"
        "⏳ Kod kelishini kuting.\n"
        "⚠️ Ishingiz bitgach akkauntdan chiqing.",
        parse_mode="Markdown",
        reply_markup=main_menu()
    )


# ===== KABINET =====
@dp.message_handler(text="💼 Kabinet")
async def cabinet(message: types.Message):
    await message.answer(
        f"👤 ID: <code>{message.from_user.id}</code>\n"
        "💰 Balans: hozircha mavjud emas",
        parse_mode="HTML"
    )


# ===== TO‘LOV =====
@dp.message_handler(text="💳 To‘lov qilish")
async def payment_start(message: types.Message):
    await message.answer("💰 Summani kiriting (so‘mda):")
    await PaymentState.waiting_sum.set()


@dp.message_handler(state=PaymentState.waiting_sum)
async def get_sum(message: types.Message, state: FSMContext):
    if not message.text.isdigit():
        await message.answer("❌ Faqat raqam kiriting")
        return

    await state.update_data(summa=message.text)

    await message.answer(
        "💳 *To‘lov ma’lumotlari:*\n\n"
        "💳 Karta: 8600 1234 5678 9012\n"
        "📱 Ulangan nomer: +998 90 123 45 67\n"
        "👤 Egasi: *Baxtiyorov Baxtiyor*\n\n"
        "📸 Endi chekni yuboring",
        parse_mode="Markdown"
    )
    await PaymentState.waiting_check.set()


@dp.message_handler(content_types=types.ContentType.PHOTO, state=PaymentState.waiting_check)
async def get_check(message: types.Message, state: FSMContext):
    data = await state.get_data()
    summa = data["summa"]
    user_id = message.from_user.id
    username = message.from_user.username or "username yo‘q"

    # Userga
    await message.answer(
        "⏳ Chek qabul qilindi.\nAdmin tasdiqlashini kuting.",
        reply_markup=main_menu()
    )
    # Adminga
    await bot.send_photo(
        chat_id=ADMIN_ID,
        photo=message.photo[-1].file_id,
        caption=(
            "🧾 *Yangi to‘lov*\n\n"
            f"👤 User: @{username}\n"
            f"🆔 ID: {user_id}\n"
            f"💰 Summa: *{summa} so‘m*"
        ),
        parse_mode="Markdown",
        reply_markup=admin_payment_kb(user_id)
    )

    await state.finish()


# ===== ADMIN TASDIQLASH / RAD ETISH =====
@dp.callback_query_handler(lambda c: c.data.startswith("pay_"))
async def admin_payment_action(call: types.CallbackQuery):
    if call.from_user.id != ADMIN_ID:
        await call.answer("❌ Siz admin emassiz", show_alert=True)
        return

    action, user_id = call.data.split(":")
    user_id = int(user_id)

    if action == "pay_ok":
        await bot.send_message(user_id, "✅ To‘lov tasdiqlandi!")
        await call.message.edit_caption(
            call.message.caption + "\n\n✅ *Tasdiqlandi*",
            parse_mode="Markdown"
        )

    elif action == "pay_no":
        await bot.send_message(user_id, "❌ To‘lov rad etildi.")
        await call.message.edit_caption(
            call.message.caption + "\n\n❌ *Rad etildi*",
            parse_mode="Markdown"
        )

    await call.answer()


# ===== RUN =====
if name == "main":
    executor.start_polling(dp, skip_updates=True)
