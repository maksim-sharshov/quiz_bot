from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message

import bot.keyboards.admin.questions_add as k
import bot.keyboards.admin.start as k_start
import bot.templates.admin.category_view as t_view
import bot.templates.admin.questions_add as t
import bot.utils as u
import db.psql.crud.admin as db_admin

router = Router(name="admin_questions_add")


async def _render_categories(callback: CallbackQuery) -> None:
    categories = await db_admin.get_categories()
    if not categories:
        await callback.message.edit_text(t.no_categories_msg, reply_markup=k.no_categories_keyb())
        return
    await callback.message.edit_text(
        t.choose_category_msg, reply_markup=k.categories_keyb(categories)
    )


@router.callback_query(k_start.AdminMenuCB.filter(F.action == "add_questions"))
async def menu_add_questions(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await _render_categories(callback)
    await callback.answer()


@router.callback_query(k.AddQuestionsCB.filter(F.action == "choose"))
async def choose_category(callback: CallbackQuery, callback_data: k.AddQuestionsCB, state: FSMContext):
    category = await db_admin.get_category(callback_data.category_id)
    if category is None:
        await callback.answer(t_view.element_deleted_msg, show_alert=True)
        await _render_categories(callback)
        return

    await state.set_state(u.QuizState.waiting_questions_file)
    await state.update_data(category_id=category.id, parsed_questions=None)
    await callback.message.edit_text(f"{t.ask_file_msg(category.title)}\n\n{t.file_hint_msg}")
    await callback.answer()


@router.message(u.QuizState.waiting_questions_file, F.document)
async def receive_file(message: Message, state: FSMContext):
    data = await state.get_data()
    category_id = data.get("category_id")
    category = await db_admin.get_category(category_id) if category_id else None
    if category is None:
        await state.clear()
        await message.answer(t.no_categories_msg, reply_markup=k.no_categories_keyb())
        return

    document = message.document
    filename = (document.file_name or "").lower()
    if not filename.endswith(".json"):
        await message.answer(t.wrong_ext_msg)
        return

    raw = await message.bot.download(document)
    questions, error = u.parse_and_validate(raw.read())

    if error is not None:
        code, index = error
        await message.answer(t.error_msg(code, index))
        await message.answer(t.file_hint_msg)
        return

    await state.update_data(parsed_questions=questions)

    chunks = t.questions_preview(questions)
    for chunk in chunks[:-1]:
        await message.answer(chunk)
    await message.answer(chunks[-1], reply_markup=k.confirm_keyb(category.id))


@router.message(u.QuizState.waiting_questions_file)
async def wrong_content(message: Message):
    await message.answer(f"{t.wrong_ext_msg}\n\n{t.file_hint_msg}")


@router.callback_query(k.AddQuestionsCB.filter(F.action == "confirm"))
async def confirm_add(callback: CallbackQuery, callback_data: k.AddQuestionsCB, state: FSMContext):
    data = await state.get_data()
    questions = data.get("parsed_questions")
    category = await db_admin.get_category(callback_data.category_id)

    if not questions or category is None:
        await state.clear()
        await callback.answer(t_view.element_deleted_msg, show_alert=True)
        await callback.message.edit_text(t.no_categories_msg, reply_markup=k_start.main_menu_keyb)
        return

    added = await db_admin.add_questions(category.id, questions)
    total = await db_admin.count_questions(category.id)
    await state.clear()
    await callback.message.edit_text(t.added_msg(added, total), reply_markup=k_start.main_menu_keyb)
    await callback.answer()


@router.callback_query(k.AddQuestionsCB.filter(F.action == "cancel"))
async def cancel_add(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await callback.message.edit_text(t.cancelled_msg, reply_markup=k_start.main_menu_keyb)
    await callback.answer()
