from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class AdminMenuCB(CallbackData, prefix="a_menu"):
    """Действия главного меню администратора."""

    action: str


main_menu_keyb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Создать категорию",
                callback_data=AdminMenuCB(action="create_category").pack(),
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            InlineKeyboardButton(
                text="Посмотреть категорию",
                callback_data=AdminMenuCB(action="view_categories").pack(),
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            InlineKeyboardButton(
                text="Добавить вопросы",
                callback_data=AdminMenuCB(action="add_questions").pack(),
                style=ButtonStyle.PRIMARY,
            )
        ],
        [
            InlineKeyboardButton(
                text="Создать квиз",
                callback_data=AdminMenuCB(action="create_quiz").pack(),
                style=ButtonStyle.SUCCESS,
            )
        ],
    ]
)
