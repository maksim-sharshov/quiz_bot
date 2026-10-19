from aiogram import F, Router
from aiogram.types import CallbackQuery

import bot.keyboards.admin.category_view as k
import bot.keyboards.admin.start as k_start
import bot.templates.admin.category_view as t
from bot.utils.constants import QUESTIONS_PAGE_SIZE
import db.psql.crud.admin as db_admin

router = Router(name="admin_category_view")


async def _render_categories(callback: CallbackQuery, page: int) -> None:
    """Показать список категорий (или заглушку)."""
    categories = await db_admin.get_categories()
    if not categories:
        await callback.message.edit_text(t.no_categories_msg, reply_markup=k.no_categories_keyb())
        return
    await callback.message.edit_text(
        t.categories_msg, reply_markup=k.categories_keyb(categories, page)
    )


async def _render_questions(callback: CallbackQuery, category_id: int, page: int) -> None:
    """Показать список вопросов категории (или заглушку / сообщение об удалении)."""
    category = await db_admin.get_category(category_id)
    if category is None:
        await callback.answer(t.element_deleted_msg, show_alert=True)
        await _render_categories(callback, 0)
        return

    questions = await db_admin.get_questions(category_id)
    if not questions:
        await callback.message.edit_text(
            t.no_questions_msg(category.title),
            reply_markup=k.questions_page_keyb(category_id, [], 0),
        )
        return

    pages = max(1, (len(questions) + QUESTIONS_PAGE_SIZE - 1) // QUESTIONS_PAGE_SIZE)
    page = max(0, min(page, pages - 1))

    await callback.message.edit_text(
        t.questions_msg(category.title),
        reply_markup=k.questions_page_keyb(category_id, questions, page),
    )


@router.callback_query(k_start.AdminMenuCB.filter(F.action == "view_categories"))
async def view_categories(callback: CallbackQuery):
    await _render_categories(callback, 0)
    await callback.answer()


@router.callback_query(k.CategoryPageCB.filter())
async def page_categories(callback: CallbackQuery, callback_data: k.CategoryPageCB):
    await _render_categories(callback, callback_data.page)
    await callback.answer()


@router.callback_query(k.CategoryOpenCB.filter())
async def open_category(callback: CallbackQuery, callback_data: k.CategoryOpenCB):
    await _render_questions(callback, callback_data.category_id, 0)
    await callback.answer()


@router.callback_query(k.QuestionPageCB.filter())
async def page_questions(callback: CallbackQuery, callback_data: k.QuestionPageCB):
    await _render_questions(callback, callback_data.category_id, callback_data.page)
    await callback.answer()


@router.callback_query(k.QuestionOpenCB.filter())
async def open_question(callback: CallbackQuery, callback_data: k.QuestionOpenCB):
    category = await db_admin.get_category(callback_data.category_id)
    question = await db_admin.get_question(callback_data.question_id)

    if category is None or question is None:
        await callback.answer(t.element_deleted_msg, show_alert=True)
        await _render_questions(callback, callback_data.category_id, 0)
        return

    questions = await db_admin.get_questions(callback_data.category_id)
    number = next(
        (index for index, item in enumerate(questions, start=1) if item.id == question.id),
        1,
    )

    await callback.message.edit_text(
        t.question_detail_msg(number, question.text, question.options),
        reply_markup=k.question_detail_keyb(callback_data.category_id, question.id),
    )
    await callback.answer()


@router.callback_query(k.QuestionDeleteCB.filter())
async def delete_question(callback: CallbackQuery, callback_data: k.QuestionDeleteCB):
    """Удаление вопроса без подтверждения, сразу показываем обновлённый список."""
    question = await db_admin.get_question(callback_data.question_id)
    if question is None:
        await callback.answer(t.element_deleted_msg, show_alert=True)
    else:
        await db_admin.delete_question(callback_data.question_id)
        await callback.answer(t.question_deleted_msg)

    await _render_questions(callback, callback_data.category_id, 0)


@router.callback_query(k.CategoryDeleteCB.filter(F.action == "ask"))
async def ask_delete_category(callback: CallbackQuery, callback_data: k.CategoryDeleteCB):
    category = await db_admin.get_category(callback_data.category_id)
    if category is None:
        await callback.answer(t.element_deleted_msg, show_alert=True)
        await _render_categories(callback, 0)
        return

    if await db_admin.category_in_active_room(category.id):
        await callback.answer(t.category_in_room_msg, show_alert=True)
        return

    count = await db_admin.count_questions(category.id)
    await callback.message.edit_text(
        t.category_delete_confirm_msg(category.title, count),
        reply_markup=k.category_delete_confirm_keyb(category.id),
    )
    await callback.answer()


@router.callback_query(k.CategoryDeleteCB.filter(F.action == "confirm"))
async def confirm_delete_category(callback: CallbackQuery, callback_data: k.CategoryDeleteCB):
    category = await db_admin.get_category(callback_data.category_id)
    if category is None:
        await callback.answer(t.element_deleted_msg, show_alert=True)
        await _render_categories(callback, 0)
        return

    if await db_admin.category_in_active_room(category.id):
        await callback.answer(t.category_in_room_msg, show_alert=True)
        await _render_questions(callback, category.id, 0)
        return

    await db_admin.delete_category_with_questions(category.id)
    await callback.message.edit_text(
        t.category_deleted_msg(category.title), reply_markup=k_start.main_menu_keyb
    )
    await callback.answer()


@router.callback_query(k.CategoryDeleteCB.filter(F.action == "cancel"))
async def cancel_delete_category(callback: CallbackQuery, callback_data: k.CategoryDeleteCB):
    await _render_questions(callback, callback_data.category_id, 0)
    await callback.answer()
