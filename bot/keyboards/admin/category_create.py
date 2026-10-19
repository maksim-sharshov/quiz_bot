from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import bot.keyboards.admin.start as k_start


class CategoryCreateCB(CallbackData, prefix="a_cc"):
    """Подтверждение или отмена черновика категории."""

    action: str


confirm_keyb = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="Подтвердить",
                callback_data=CategoryCreateCB(action="confirm").pack(),
                style=ButtonStyle.SUCCESS,
            ),
            InlineKeyboardButton(
                text="Удалить",
                callback_data=CategoryCreateCB(action="cancel").pack(),
                style=ButtonStyle.DANGER,
            ),
        ],
        [
            InlineKeyboardButton(
                text="🏠 В меню",
                callback_data=k_start.AdminMenuCB(action="menu").pack(),
                style=ButtonStyle.PRIMARY,
            )
        ],
    ]
)
