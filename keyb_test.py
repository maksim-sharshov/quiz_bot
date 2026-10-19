import asyncio
import logging
import sys
from aiogram import Bot, Dispatcher, F
from aiogram.enums import ButtonStyle
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message

TOKEN = ""
dp = Dispatcher()


class QuizState(StatesGroup):
    voting = State()


def get_poll_keyboard(selected_items: set):
    options = [
        ("Python", "opt_python"),
        ("JavaScript", "opt_js"),
        ("C++", "opt_cpp"),
    ]

    keyboard = []
    for text, cb_data in options:
        is_selected = cb_data in selected_items
        btn_style = ButtonStyle.SUCCESS if is_selected else None
        btn_text = f"✅ {text}" if is_selected else text

        keyboard.append([
            InlineKeyboardButton(
                text=btn_text,
                callback_data=cb_data,
                style=btn_style,
            )
        ])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def get_timer_bar(current: int, total: int = 5) -> str:
    return "🟩" * current + "⬜" * (total - current)


@dp.message(Command("poll"))
async def cmd_poll(message: Message, state: FSMContext):
    await state.set_state(QuizState.voting)
    await state.update_data(selected=[])

    total_seconds = 5
    bar = get_timer_bar(total_seconds, total_seconds)
    keyboard = get_poll_keyboard(set())

    msg = await message.answer(
        f"🗳 **Выберите один или несколько вариантов ответа:**\n\n"
        f"Шкала времени: `{bar}`\n"
        f"Осталось секунд: **{total_seconds}**",
        reply_markup=keyboard,
    )

    # Сохраняем ID сообщения в FSM, чтобы обработчик кликов знал, что обновлять
    await state.update_data(msg_id=msg.message_id)

    # Цикл обратного отсчета
    for seconds_left in range(total_seconds - 1, 0, -1):
        await asyncio.sleep(1.0)
        try:
            bar = get_timer_bar(seconds_left, total_seconds)
            data = await state.get_data()
            current_selected = set(data.get("selected", []))

            await msg.edit_text(
                f"🗳 **Выберите один или несколько вариантов ответа:**\n\n"
                f"Шкала времени: `{bar}`\n"
                f"Осталось секунд: **{seconds_left}**",
                reply_markup=get_poll_keyboard(current_selected),
            )
        except Exception:
            break

    # Финальная фаза: время вышло
    await asyncio.sleep(1.0)
    try:
        data = await state.get_data()
        final_selected = data.get("selected", [])

        options_map = {
            "opt_python": "Python",
            "opt_js": "JavaScript",
            "opt_cpp": "C++"
        }
        chosen_names = [options_map[item] for item in final_selected]
        result_text = ", ".join(chosen_names) if chosen_names else "ничего не выбрано"

        await msg.edit_text(
            f"⏰ **Время вышло!** Опрос завершен.\n\n"
            f"Ваш итоговый выбор: **{result_text}**",
            reply_markup=None,
        )

        await state.clear()

        await asyncio.sleep(1.5)
        await msg.delete()
        await message.answer(f"🚀 Спасибо за участие! Зафиксирован выбор: {result_text}. Переходим дальше.")

    except Exception as e:
        logging.error(f"Ошибка таймера опроса: {e}")
        await state.clear()


# Обработчик нажатий — теперь срабатывает мгновенно и обновляет интерфейс без задержки
@dp.callback_query(QuizState.voting, F.data.in_({"opt_python", "opt_js", "opt_cpp"}))
async def process_poll_choice(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    selected_list = data.get("selected", [])
    selected_set = set(selected_list)

    choice = callback.data

    if choice in selected_set:
        selected_set.remove(choice)
        await callback.answer("Выбор отменен")
    else:
        selected_set.add(choice)
        await callback.answer("Выбор сохранен!")

    # Обновляем состояние в FSM
    await state.update_data(selected=list(selected_set))

    # Мгновенно перерисовываем кнопки по клику пользователя
    try:
        await callback.message.edit_reply_markup(reply_markup=get_poll_keyboard(selected_set))
    except Exception:
        pass


async def main():
    bot = Bot(token=TOKEN)
    await dp.start_polling(bot)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, stream=sys.stdout)
    asyncio.run(main())
