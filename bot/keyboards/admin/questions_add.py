from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.admin.start import AdminMenuCB


class AddQuestionsCB(CallbackData, prefix="a_qadd"):
    """Выбор категории, подтверждение или отмена добавления вопросов."""

    action: str
    category_id: int = 0


def categories_keyb(categories: list) -> InlineKeyboardMarkup:
    """Список категорий для добавления вопросов."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=category.title[:60],
                callback_data=AddQuestionsCB(action="choose", category_id=category.id).pack(),
            )
        ]
        for category in categories
    ]
    rows.append(
        [InlineKeyboardButton(text="Назад в меню", callback_data=AdminMenuCB(action="menu").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)


def no_categories_keyb() -> InlineKeyboardMarkup:
    """Заглушка, когда категорий нет."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Создать категорию",
                    callback_data=AdminMenuCB(action="create_category").pack(),
                    style=ButtonStyle.SUCCESS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад в меню", callback_data=AdminMenuCB(action="menu").pack()
                )
            ],
        ]
    )


def confirm_keyb(category_id: int) -> InlineKeyboardMarkup:
    """Подтверждение добавления распарсенных вопросов."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Добавить",
                    callback_data=AddQuestionsCB(action="confirm", category_id=category_id).pack(),
                    style=ButtonStyle.SUCCESS,
                )
            ],
            [
                InlineKeyboardButton(
                    text="Удалить",
                    callback_data=AddQuestionsCB(action="cancel", category_id=category_id).pack(),
                    style=ButtonStyle.DANGER,
                )
            ],
        ]
    )
