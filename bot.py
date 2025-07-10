from aiogram import Bot, Dispatcher, executor, types
from dotenv import load_dotenv
import logging
import os

load_dotenv()
API_TOKEN = os.getenv("API_TOKEN")
CHANNEL_USERNAME = '@poryadindom'
BONUS_LINK = 'https://ваш_бонус_или_файл'

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

@dp.message_handler(commands=['start'])
async def start_handler(message: types.Message):
    await message.answer(
        "🎁 Хочешь получить подарок?\n\n"
        "1. Подпишись на наш канал: @poryadindom\n"
        "2. Нажми кнопку ниже, чтобы получить вкусняшку!",
        reply_markup=types.InlineKeyboardMarkup().add(
            types.InlineKeyboardButton("✅ Я подписался", callback_data="check_sub")
        )
    )

@dp.callback_query_handler(lambda c: c.data == 'check_sub')
async def check_subscription(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    try:
        member = await bot.get_chat_member(chat_id=CHANNEL_USERNAME, user_id=user_id)
        logging.info(f"Проверка подписки: пользователь {user_id}, статус: {member.status}")
        if member.status in ['member', 'administrator', 'creator']:
            await callback_query.message.answer(f"🎉 Спасибо за подписку, лови вкусняшку): {BONUS_LINK}")
        else:
            await callback_query.message.answer("❌ Халтурить не надо, сначала подпишитесь на канал и попробуйте снова.")
    except Exception as e:
        logging.error(f"Ошибка при проверке подписки у пользователя {user_id}: {e}")
        await callback_query.message.answer("⚠️ Не удалось проверить подписку. Попробуйте позже.")

    await callback_query.answer()

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
