from aiogram import Router
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

import bot.keyboards.user.game as k
import bot.services as s
import bot.templates.user.game as t

router = Router(name="user_game")


@router.callback_query(k.AnswerCB.filter())
async def choose_answer(callback: CallbackQuery, callback_data: k.AnswerCB, state: FSMContext):
    """Выбор или снятие варианта ответа. Нажатия старого вопроса игнорируются."""
    data = await state.get_data()

    is_stale = (
        data.get("finished")
        or data.get("question_id") != callback_data.question_id
        or data.get("room_id") != callback_data.room_id
    )
    if is_stale:
        await callback.answer(t.stale_answer_msg)
        return

    options = data.get("options", [])
    if not 0 <= callback_data.option < len(options):
        await callback.answer(t.stale_answer_msg)
        return

    selected = set(data.get("selected", []))
    if callback_data.option in selected:
        selected.discard(callback_data.option)
        await callback.answer(t.choice_cancelled_msg)
    else:
        selected.add(callback_data.option)
        await callback.answer(t.choice_saved_msg)

    await state.update_data(selected=sorted(selected))

    await s.broadcast.safe_edit_markup(
        callback.bot,
        callback.message.chat.id,
        callback.message.message_id,
        k.answer_keyb(callback_data.room_id, callback_data.question_id, options, selected),
    )
