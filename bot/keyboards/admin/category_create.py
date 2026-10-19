from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


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
        ]
    ]
)
