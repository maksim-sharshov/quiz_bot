from aiogram import Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

import bot.keyboards.user.room as k_room
import bot.services as s
import bot.templates.user.commands as t
import bot.templates.user.room as t_room
import bot.utils as u
import db.psql.crud.admin as db_admin
from db.psql.models.models import Users

router = Router(name="user_commands")


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
    room = await db_admin.get_room_by_code(code)
    if room is None:
        await message.answer(t.room_not_found_msg)
        return

    if room.status in (u.ROOM_FINISHED, u.ROOM_INTERRUPTED):
        await message.answer(t.room_finished_msg)
        return
    if room.status != u.ROOM_OPEN:
        await message.answer(t.room_closed_msg)
        return

    status = await s.room.try_join(
        message.bot, room, message.from_user.id, message.from_user.username
    )
    if status == "busy":
        await message.answer(t.already_in_room_msg)
        return
    if status == "already":
        await message.answer(t.already_joined_msg)
        return

    category = await db_admin.get_category(room.category_id)
    title = category.title if category else ""
    count = await db_admin.count_active_players(room.id)

    lobby = await message.answer(
        t_room.room_lobby_msg(title, room.timer_sec, count),
        reply_markup=k_room.room_lobby_keyb(room.id),
    )
    await db_admin.set_lobby_message(room.id, message.from_user.id, lobby.message_id)
    await s.room.refresh_room_messages(message.bot, room)
