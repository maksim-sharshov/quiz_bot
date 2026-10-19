from aiogram.filters import BaseFilter
from aiogram.types import TelegramObject

from settings import settings


class IsAdmin(BaseFilter):
    """
    Пропускает событие, только если его отправил администратор.
    Работает и для Message, и для CallbackQuery.
    """

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        admins = settings.bot.ADMINS or []
        return bool(user and user.id in admins)
