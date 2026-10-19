from aiogram.filters import BaseFilter
from aiogram.types import Message, TelegramObject

from settings import settings
from db.psql.models.models import Users


class NewUser(BaseFilter):
    """
    Проверить, что пользователя ещё нет в базе данных.
    """

    async def __call__(self, msg: Message) -> bool:
        user_id = await Users.check(tg_id=msg.from_user.id)
        return not bool(user_id)


class IsPlayer(BaseFilter):
    """
    Пропускает событие, только если его отправил рядовой игрок (не админ).
    Работает и для Message, и для CallbackQuery.
    """

    async def __call__(self, event: TelegramObject) -> bool:
        user = getattr(event, "from_user", None)
        if not user:
            return False
        admins = settings.bot.ADMINS or []
        return user.id not in admins
