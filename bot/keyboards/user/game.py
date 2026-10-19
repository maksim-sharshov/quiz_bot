from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class AnswerCB(CallbackData, prefix="u_ans"):
    """Выбор варианта ответа игроком (привязан к комнате и вопросу)."""

    room_id: int
    question_id: int
    option: int


def answer_keyb(
    room_id: int,
    question_id: int,
    options: list[dict],
    selected: set[int],
) -> InlineKeyboardMarkup:
    """
    Клавиатура вариантов ответа.
    Выбранный вариант — зелёный и с галочкой ✅.
    """
    rows: list[list[InlineKeyboardButton]] = []
    for index, option in enumerate(options):
        is_selected = index in selected
        rows.append(
            [
                InlineKeyboardButton(
                    text=f"✅ {option['text']}" if is_selected else option["text"],
                    callback_data=AnswerCB(
                        room_id=room_id,
                        question_id=question_id,
                        option=index,
                    ).pack(),
                    style=ButtonStyle.SUCCESS if is_selected else None,
                )
            ]
        )
    return InlineKeyboardMarkup(inline_keyboard=rows)


# Пустая клавиатура — используется, чтобы убрать кнопки у сообщения
empty_keyb = InlineKeyboardMarkup(inline_keyboard=[])
