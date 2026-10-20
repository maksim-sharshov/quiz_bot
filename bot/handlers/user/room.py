from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import bot.keyboards.user.room as k
import bot.services as s
import bot.templates.user.room as t
import db.psql.crud.admin as db_admin

router = Router(name="user_room")


@router.callback_query(k.RoomLeaveCB.filter())
async def leave_room(callback: CallbackQuery, callback_data: k.RoomLeaveCB, state: FSMContext):
    """Выход игрока из комнаты."""
    room = await db_admin.get_room(callback_data.room_id)
    if room is not None:
        await s.room.leave_player(callback.bot, room, callback.from_user.id)

    await state.clear()
    await callback.message.edit_text(t.you_left_msg, reply_markup=k.empty_keyb)
    await callback.answer()
