from aiogram import F, Router
from aiogram.filters import Command, CommandObject
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.keyboards.admin.start as k
import bot.services as s
import bot.templates.admin.start as t
import bot.templates.user.commands as t_user

router = Router(name="admin_start")

_JOIN_STATUS_TEXTS = {
    "not_found": t_user.room_not_found_msg,
    "finished": t_user.room_finished_msg,
    "closed": t_user.room_closed_msg,
    "busy": t_user.already_in_room_msg,
    "already": t_user.already_joined_msg,
}


@router.message(Command("start"))
async def admin_start(message: Message, command: CommandObject, state: FSMContext):
    """
    Команда /start у администратора: показываем главное меню.
    Deep-link `room_<код>` позволяет администратору войти в игру как игрок.
    """
    await state.clear()

    payload = (command.args or "").strip()
    if payload.startswith("room_"):
        status = await s.room.enter_room(
            message.bot,
            message.chat.id,
            message.from_user.id,
            message.from_user.username,
            payload[len("room_"):],
        )
        text = _JOIN_STATUS_TEXTS.get(status)
        if text:
            await message.answer(text)
        return

    await message.answer(t.start_msg, reply_markup=k.main_menu_keyb)


@router.callback_query(k.AdminMenuCB.filter(F.action == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(t.start_msg, reply_markup=k.main_menu_keyb)
    await callback.answer()
