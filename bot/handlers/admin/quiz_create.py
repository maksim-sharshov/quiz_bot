from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import bot.keyboards.admin.quiz_create as k
import bot.keyboards.admin.room as k_room
import bot.keyboards.admin.start as k_start
import bot.services as s
import bot.templates.admin.category_view as t_view
import bot.templates.admin.quiz_create as t
import bot.templates.admin.room as t_room
import bot.utils as u
import db.psql.crud.admin as db_admin

router = Router(name="admin_quiz_create")


async def _render_categories(callback: CallbackQuery) -> None:
    categories = await db_admin.get_categories()
    if not categories:
        await callback.message.edit_text(t.no_categories_msg, reply_markup=k.no_categories_keyb())
        return
    await callback.message.edit_text(
        t.choose_category_msg, reply_markup=k.categories_keyb(categories)
    )


@router.callback_query(k_start.AdminMenuCB.filter(F.action == "create_quiz"))
async def menu_create_quiz(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _render_categories(callback)
    await callback.answer()


@router.callback_query(k.QuizCategoryCB.filter())
async def choose_category(callback: CallbackQuery, callback_data: k.QuizCategoryCB, state: FSMContext):
    category = await db_admin.get_category(callback_data.category_id)
    if category is None:
        await callback.answer(t_view.element_deleted_msg, show_alert=True)
        await _render_categories(callback)
        return

    questions = await db_admin.count_questions(category.id)
    if questions == 0:
        await callback.message.edit_text(
            t.no_questions_msg(category.title), reply_markup=k.back_to_menu_keyb()
        )
        await callback.answer()
        return

    await state.set_state(u.QuizState.waiting_timer)
    await state.update_data(category_id=category.id)
    await callback.message.edit_text(
        t.choose_timer_msg(category.title), reply_markup=k.timer_keyb(category.id)
    )
    await callback.answer()


@router.callback_query(k.QuizTimerCB.filter())
async def choose_timer(callback: CallbackQuery, callback_data: k.QuizTimerCB, state: FSMContext):
    if callback_data.timer not in u.TIMER_CHOICES:
        await callback.answer(t_view.element_deleted_msg, show_alert=True)
        return

    category = await db_admin.get_category(callback_data.category_id)
    if category is None:
        await state.clear()
        await callback.answer(t_view.element_deleted_msg, show_alert=True)
        await _render_categories(callback)
        return

    room = await s.room.create_room(
        bot=callback.bot,
        admin_tg_id=callback.from_user.id,
        admin_chat_id=callback.message.chat.id,
        category_id=category.id,
        timer_sec=callback_data.timer,
    )
    link = await s.room.invite_link(callback.bot, room.code)

    panel = await callback.message.answer(
        t_room.room_panel_msg(category.title, room.timer_sec, 0, link),
        reply_markup=k_room.room_control_keyb(room.id),
    )
    await db_admin.set_admin_message(room.id, panel.message_id)

    await state.clear()
    await callback.answer()
