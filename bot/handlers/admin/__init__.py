from aiogram import F, Router

from bot.filters.admin import IsAdmin
from bot.handlers.admin.start import router as start_router
from bot.handlers.admin.category_create import router as category_create_router
from bot.handlers.admin.category_view import router as category_view_router
from bot.handlers.admin.questions_add import router as questions_add_router
from bot.handlers.admin.quiz_create import router as quiz_create_router
from bot.handlers.admin.room import router as room_router

router = Router(name="admin")
router.message.filter(F.chat.type == "private", IsAdmin())
router.callback_query.filter(IsAdmin())

router.include_router(start_router)
router.include_router(category_create_router)
router.include_router(category_view_router)
router.include_router(questions_add_router)
router.include_router(quiz_create_router)
router.include_router(room_router)
