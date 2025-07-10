import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import Message
from aiogram.enums import ParseMode
from aiogram.filters import Command

TOKEN = "7711367749:AAGMgqf_G703pzE0MOKleeE8VsPR6w5zb54"

bot = Bot(token=TOKEN, parse_mode=ParseMode.HTML)
dp = Dispatcher()

@dp.message(Command("start"))
async def start_handler(message: Message):
    await message.answer("Привет! Я твой бот")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
