from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class RoomLeaveCB(CallbackData, prefix="u_leave"):
    """Выход игрока из комнаты."""

    room_id: int


def room_lobby_keyb(room_id: int) -> InlineKeyboardMarkup:
    """Клавиатура лобби игрока: красная кнопка «Выйти»."""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="Выйти",
                    callback_data=RoomLeaveCB(room_id=room_id).pack(),
                    style=ButtonStyle.DANGER,
                )
            ]
        ]
    )
