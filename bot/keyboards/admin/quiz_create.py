from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot.keyboards.admin.start import AdminMenuCB
from bot.utils.constants import TIMER_CHOICES


class QuizCategoryCB(CallbackData, prefix="a_qz_cat"):
    category_id: int


class QuizTimerCB(CallbackData, prefix="a_qz_timer"):
    category_id: int
    timer: int


def categories_keyb(categories: list) -> InlineKeyboardMarkup:
    """Выбор категории для квиза."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=category.title[:60],
                callback_data=QuizCategoryCB(category_id=category.id).pack(),
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


def back_to_menu_keyb() -> InlineKeyboardMarkup:
    """Кнопка «Назад» в главное меню."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Назад", callback_data=AdminMenuCB(action="menu").pack()
                )
            ]
        ]
    )


def timer_keyb(category_id: int) -> InlineKeyboardMarkup:
    """Выбор таймера на вопрос."""
    rows: list[list[InlineKeyboardButton]] = [
        [
            InlineKeyboardButton(
                text=f"{seconds} сек",
                callback_data=QuizTimerCB(category_id=category_id, timer=seconds).pack(),
                style=ButtonStyle.PRIMARY,
            )
        ]
        for seconds in TIMER_CHOICES
    ]
    rows.append(
        [InlineKeyboardButton(text="Назад в меню", callback_data=AdminMenuCB(action="menu").pack())]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
