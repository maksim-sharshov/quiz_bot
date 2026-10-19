from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import bot.services as s
import bot.templates.user.commands as t
from db.psql.models.models import Users

router = Router(name="user_commands")

_JOIN_STATUS_TEXTS = {
    "not_found": t.room_not_found_msg,
    "finished": t.room_finished_msg,
    "closed": t.room_closed_msg,
    "busy": t.already_in_room_msg,
    "already": t.already_joined_msg,
}


@router.message(Command("start"))
async def start(message: Message, command: CommandObject, state: FSMContext):
    """
    /start игрока. Поддерживает deep-link `room_<код>` для входа в комнату.
    """
    await state.clear()

    tg_id = message.from_user.id
    if not await Users.check(tg_id=tg_id):
        await Users.create(tg_id=tg_id, username=message.from_user.username)

    payload = (command.args or "").strip()
    if payload.startswith("room_"):
        await _join_room(message, state, payload[len("room_"):])
        return

    await message.answer(t.greeting_msg)


async def _join_room(message: Message, state: FSMContext, code: str) -> None:
    """Вход игрока в комнату по коду."""
    status = await s.room.enter_room(
        message.bot, message.chat.id, message.from_user.id, message.from_user.username, code
    )
    text = _JOIN_STATUS_TEXTS.get(status)
    if text:
        await message.answer(text)
