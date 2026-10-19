import logging
import asyncio
from aiogram import Dispatcher
from aiogram.types import BotCommandScopeDefault

from core.bot import bot
from bot.handlers import routers
import bot.services as s

from settings import settings
from db.psql.crud.base import init_postgres


logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)


dp = Dispatcher()
dp.include_routers(*routers)


async def main():

    await init_postgres()

    # Активные квизы при перезапуске помечаем прерванными и уведомляем участников
    await s.room.cleanup_interrupted(bot)

    await bot.set_my_commands(
        commands=settings.bot.COMMANDS,
        scope=BotCommandScopeDefault()
    )

    await dp.start_polling(bot)


if __name__ == "__main__":

    try:
        logging.info("✅ Бот запущен!")
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.error("🛑 Бот остановлен вручную!")

    except Exception as e:
        logging.error(f"❌ Возникла критическая ошибка: {type(e).__name__}: {e}")
