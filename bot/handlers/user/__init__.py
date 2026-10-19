from aiogram import F, Router

from bot.filters.user import IsPlayer
from bot.handlers.user.commands import router as commands_router
from bot.handlers.user.room import router as room_router
from bot.handlers.user.game import router as game_router

router = Router(name="user")
router.message.filter(F.chat.type == "private", IsPlayer())
router.callback_query.filter(IsPlayer())

router.include_router(commands_router)
router.include_router(room_router)
router.include_router(game_router)
