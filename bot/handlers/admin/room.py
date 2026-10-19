from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import bot.keyboards.admin.room as k
import bot.services as s
import bot.templates.admin.room as t
import bot.utils as u
import db.psql.crud.admin as db_admin

router = Router(name="admin_room")

_FINISHED_STATUSES = (u.ROOM_FINISHED, u.ROOM_INTERRUPTED)


@router.callback_query(k.RoomControlCB.filter(F.action == "start"))
async def start_quiz(callback: CallbackQuery, callback_data: k.RoomControlCB, state: FSMContext):
    """Запустить квиз."""
    room = await db_admin.get_room(callback_data.room_id)
    if room is None or room.status in _FINISHED_STATUSES:
        await callback.answer(t.room_gone_msg, show_alert=True)
        return

    if room.status == u.ROOM_IN_PROGRESS or s.game.is_running(room.id):
        await callback.answer(t.already_running_msg, show_alert=True)
        return

    count = await db_admin.count_active_players(room.id)
    if count == 0:
        await callback.answer(t.need_players_msg, show_alert=True)
        return

    started = await s.game.start_quiz(callback.bot, state.storage, room)
    if not started:
        await callback.answer(t.already_running_msg, show_alert=True)
        return

    await s.room.notify_admin_started(callback.bot, room)
    await callback.answer()


@router.callback_query(k.RoomControlCB.filter(F.action == "finish"))
async def finish_quiz(callback: CallbackQuery, callback_data: k.RoomControlCB, state: FSMContext):
    """Досрочно завершить квиз и разослать итоги."""
    room = await db_admin.get_room(callback_data.room_id)
    if room is None or room.status in _FINISHED_STATUSES:
        await callback.answer(t.room_gone_msg, show_alert=True)
        return

    await s.game.finish_early(callback.bot, state.storage, room)
    await callback.answer()
