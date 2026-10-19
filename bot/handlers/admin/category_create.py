from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.keyboards.admin.category_create as k
import bot.keyboards.admin.start as k_start
import bot.templates.admin.category_create as t
import bot.utils as u
import db.psql.crud.admin as db_admin

router = Router(name="admin_category_create")


@router.callback_query(k_start.AdminMenuCB.filter(F.action == "create_category"))
async def ask_name(callback: CallbackQuery, state: FSMContext):
    """Запросить название новой категории."""
    await state.clear()
    await state.set_state(u.QuizState.waiting_category_name)
    await callback.message.edit_text(t.ask_name_msg, reply_markup=k_start.menu_keyb)
    await callback.answer()


@router.message(u.QuizState.waiting_category_name, F.text)
async def receive_name(message: Message, state: FSMContext):
    """Принять и проверить название, показать подтверждение."""
    title = (message.text or "").strip()

    if not title:
        await message.answer(t.title_empty_msg, reply_markup=k_start.menu_keyb)
        return
    if len(title) > u.MAX_CATEGORY_TITLE_LEN:
        await message.answer(t.title_long_msg, reply_markup=k_start.menu_keyb)
        return
    if await db_admin.get_category_by_title(title):
        await message.answer(t.title_duplicate_msg(title), reply_markup=k_start.menu_keyb)
        return

    await state.update_data(category_title=title)
    await message.answer(t.confirm_msg(title), reply_markup=k.confirm_keyb)


@router.callback_query(k.CategoryCreateCB.filter(F.action == "confirm"))
async def confirm_create(callback: CallbackQuery, state: FSMContext):
    """Сохранить категорию в БД."""
    data = await state.get_data()
    title = data.get("category_title")

    if not title:
        await state.clear()
        await callback.message.edit_text(t.cancelled_msg, reply_markup=k_start.main_menu_keyb)
        await callback.answer()
        return

    if await db_admin.get_category_by_title(title):
        await state.clear()
        await callback.message.edit_text(
            t.title_duplicate_msg(title), reply_markup=k_start.main_menu_keyb
        )
        await callback.answer()
        return

    await db_admin.create_category(title)
    await state.clear()
    await callback.message.edit_text(t.saved_msg(title), reply_markup=k_start.main_menu_keyb)
    await callback.answer()


@router.callback_query(k.CategoryCreateCB.filter(F.action == "cancel"))
async def cancel_create(callback: CallbackQuery, state: FSMContext):
    """Сбросить черновик категории."""
    await state.clear()
    await callback.message.edit_text(t.cancelled_msg, reply_markup=k_start.main_menu_keyb)
    await callback.answer()
