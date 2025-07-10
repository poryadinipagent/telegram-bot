import asyncio
import json
from aiogram import Bot, Dispatcher, types, F
from aiogram.types import Message, CallbackQuery, FSInputFile, ReplyKeyboardMarkup, KeyboardButton
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiocron import crontab
import os

TOKEN = os.getenv("TOKEN")
CHANNEL_USERNAME = "@poryadindom"
admin_id_str = os.getenv("ADMIN_ID")
if not admin_id_str:
    raise ValueError("ADMIN_ID environment variable is not set")
ADMIN_ID = int(admin_id_str)

PDF_FILE_PATH = "file.pdf"
USERS_FILE = "users.json"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

try:
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
except (FileNotFoundError, json.JSONDecodeError):
    users = {}

async def save_users():
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2, ensure_ascii=False)

@dp.message(CommandStart())
async def cmd_start(message: Message):
    user_id = str(message.from_user.id)
    users[user_id] = users.get(user_id, {"name": message.from_user.full_name})
    await save_users()

    member = await bot.get_chat_member(CHANNEL_USERNAME, message.from_user.id)
    if member.status not in ("member", "administrator", "creator"):
        kb = InlineKeyboardBuilder()
        kb.button(text="Подписаться на канал", url=f"https://t.me/{CHANNEL_USERNAME[1:]}")
        await message.answer("👋 Привет! Чтобы начать, пожалуйста, подпишитесь на наш канал.", reply_markup=kb.as_markup())
        return

    await ask_goal(message)

async def ask_goal(message: Message):
    kb = InlineKeyboardBuilder()
    kb.button(text="Для проживания", callback_data="goal_live")
    kb.button(text="Для инвестиций", callback_data="goal_invest")
    await message.answer("Рассматриваете недвижимость для жизни или в качестве инвестиции?", reply_markup=kb.as_markup())

@dp.callback_query(F.data.startswith("goal_"))
async def handle_goal(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    goal = callback.data.replace("goal_", "")
    users[user_id]["goal"] = goal
    await save_users()

    kb = InlineKeyboardBuilder()
    kb.button(text="1-комнатная", callback_data="type_1")
    kb.button(text="2-комнатная", callback_data="type_2")
    kb.button(text="3-комнатная", callback_data="type_3")
    kb.button(text="Дом", callback_data="type_house")
    kb.button(text="Студия", callback_data="type_studio")
    await callback.message.answer("Отлично, уточните, какой тип недвижимости вас интересует?", reply_markup=kb.as_markup())
    await callback.answer()

@dp.callback_query(F.data.startswith("type_"))
async def handle_type(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    type_ = callback.data.replace("type_", "")
    users[user_id]["type"] = type_
    await save_users()

    if users[user_id].get("goal") == "invest":
        kb = InlineKeyboardBuilder()
        kb.button(text="Краснодар", callback_data="city_krasnodar")
        kb.button(text="Москва", callback_data="city_moscow")
        kb.button(text="СПБ", callback_data="city_spb")
        kb.button(text="Побережье Краснодарского края", callback_data="city_coast")
        await callback.message.answer("Какие регионы наиболее интересны вам для вложений?", reply_markup=kb.as_markup())
    else:
        await request_contact(callback.message)

    await callback.answer()

@dp.callback_query(F.data.startswith("city_"))
async def handle_city(callback: CallbackQuery):
    user_id = str(callback.from_user.id)
    city = callback.data.replace("city_", "")
    users[user_id]["city"] = city
    await save_users()
    await request_contact(callback.message)
    await callback.answer()

async def request_contact(message: Message):
    kb = ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Оставить номер телефона", request_contact=True)]],
        resize_keyboard=True, one_time_keyboard=True
    )
    await message.answer("Спасибо! Чтобы мы могли связаться с вами, пожалуйста, оставьте ваш номер телефона.", reply_markup=kb)

@dp.message(F.contact)
async def handle_contact(message: Message):
    user_id = str(message.from_user.id)
    contact = message.contact.phone_number
    users[user_id]["phone"] = contact
    await save_users()

    name = message.from_user.full_name
    goal = users[user_id].get("goal", "—")
    type_ = users[user_id].get("type", "—")
    city = users[user_id].get("city", "—")

    msg = f"📩 Новая заявка от <b>{name}</b>\nЦель: {goal}\nТип: {type_}\nРегион: {city}\nТелефон: {contact}"
    await bot.send_message(ADMIN_ID, msg)

    if os.path.exists(PDF_FILE_PATH):
        file = FSInputFile(PDF_FILE_PATH)
        await message.answer_document(file, caption="Отлично! Вот подборка для вас. Если появятся вопросы — мы всегда на связи! 😊")
    else:
        await message.answer("Файл пока не прикреплён, но мы свяжемся с вами лично совсем скоро! 🔔")

    await message.answer("Благодарим за интерес! Мы подберём для вас лучшее предложение и свяжемся в ближайшее время. 👌", reply_markup=types.ReplyKeyboardRemove())

@dp.message()
async def smart_replies(message: Message):
    text = message.text.lower()
    if "море" in text or "побережье" in text:
        await message.answer("🏖 У нас есть отличные варианты на побережье Краснодарского края! Могу выслать примеры — просто напишите, какой формат интересен.")
    elif "цены" in text or "стоимость" in text:
        await message.answer("💰 Цены зависят от типа жилья и региона. Напишите, что вы рассматриваете, и мы подскажем актуальные предложения.")
    elif "контакт" in text or "позвоните" in text:
        await message.answer("📞 Конечно, как с вами лучше связаться? Вы можете нажать кнопку 'Оставить номер телефона' или просто напишите его сюда.")
    else:
        await message.answer("👀 Мы с интересом читаем каждое сообщение. Наш специалист свяжется с вами в ближайшее время!")

@crontab("0 12 */2 * *")
async def scheduled_message():
    for user_id in users:
        try:
            await bot.send_message(user_id, "Привет! 👋 У нас появилось несколько новых объектов, которые могут вас заинтересовать. Хотите, вышлем подборку?")
        except:
            continue

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
