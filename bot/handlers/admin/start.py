from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.keyboards.admin.start as k
import bot.templates.admin.start as t

router = Router(name="admin_start")


@router.message(Command("start"))
async def admin_start(message: Message, state: FSMContext):
    """Команда /start у администратора: показываем главное меню."""
    await state.clear()
    await message.answer(t.start_msg, reply_markup=k.main_menu_keyb)


@router.callback_query(k.AdminMenuCB.filter(F.action == "menu"))
async def back_to_menu(callback: CallbackQuery, state: FSMContext):
    """Возврат в главное меню."""
    await state.clear()
    await callback.message.edit_text(t.start_msg, reply_markup=k.main_menu_keyb)
    await callback.answer()
