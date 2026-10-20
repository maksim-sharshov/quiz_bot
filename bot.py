import logging
import asyncio
import signal

from aiogram import Bot, Dispatcher
from aiogram.types import BotCommandScopeDefault
from aiogram.webhook.aiohttp_server import SimpleRequestHandler, setup_application
from aiohttp import web

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


async def on_startup(bot: Bot) -> None:
    await init_postgres()

    # Активные квизы при перезапуске помечаем прерванными и уведомляем участников
    await s.room.cleanup_interrupted(bot)

    await bot.set_my_commands(
        commands=settings.bot.COMMANDS,
        scope=BotCommandScopeDefault()
    )

    if settings.webhook.BASE_URL:
        await bot.set_webhook(
            url=settings.webhook.URL,
            secret_token=settings.webhook.SECRET or None,
            allowed_updates=dp.resolve_used_update_types(),
            drop_pending_updates=settings.webhook.DROP_PENDING,
        )
        logging.info("Webhook установлен: %s", settings.webhook.URL)


async def on_shutdown(bot: Bot) -> None:
    await bot.session.close()


dp.startup.register(on_startup)
dp.shutdown.register(on_shutdown)


async def healthcheck(request: web.Request) -> web.Response:
    return web.Response(text="ok")


async def run_webhook() -> None:
    """Запуск HTTP-сервера, на который Telegram присылает обновления."""
    app = web.Application()
    app.router.add_get("/health", healthcheck)

    SimpleRequestHandler(
        dispatcher=dp,
        bot=bot,
        secret_token=settings.webhook.SECRET or None,
    ).register(app, path=settings.webhook.PATH)

    setup_application(app, dp, bot=bot)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host=settings.webhook.HOST, port=settings.webhook.PORT)
    await site.start()

    logging.info(
        "HTTP-сервер запущен на %s:%s, webhook path: %s",
        settings.webhook.HOST,
        settings.webhook.PORT,
        settings.webhook.PATH,
    )

    stop_event = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop_event.set)
        except (NotImplementedError, RuntimeError):
            # Windows не поддерживает add_signal_handler
            pass

    try:
        await stop_event.wait()
    finally:
        await runner.cleanup()


async def run_polling() -> None:
    """Локальный режим без публичного адреса."""
    logging.warning(
        "WEBHOOK_BASE_URL не задан — работаем через long polling. "
        "Для webhook укажите публичный HTTPS-адрес в WEBHOOK_BASE_URL."
    )
    await bot.delete_webhook(drop_pending_updates=False)
    await dp.start_polling(bot)


async def main():
    if settings.webhook.BASE_URL:
        await run_webhook()
    else:
        await run_polling()


if __name__ == "__main__":

    try:
        logging.info("✅ Бот запущен!")
        asyncio.run(main())

    except KeyboardInterrupt:
        logging.error("🛑 Бот остановлен вручную!")

    except Exception as e:
        logging.error(f"❌ Возникла критическая ошибка: {type(e).__name__}: {e}")
