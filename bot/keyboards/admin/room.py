from aiogram.enums import ButtonStyle
from aiogram.filters.callback_data import CallbackData
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


class RoomControlCB(CallbackData, prefix="a_room"):
    """Управление комнатой: начать или завершить квиз."""

    action: str
    room_id: int


def room_control_keyb(room_id: int, started: bool = False) -> InlineKeyboardMarkup:
    """Кнопки панели администратора."""
    rows: list[list[InlineKeyboardButton]] = []
    if not started:
        rows.append(
            [
                InlineKeyboardButton(
                    text="Начать квиз",
                    callback_data=RoomControlCB(action="start", room_id=room_id).pack(),
                    style=ButtonStyle.SUCCESS,
                )
            ]
        )
    rows.append(
        [
            InlineKeyboardButton(
                text="Завершить квиз",
                callback_data=RoomControlCB(action="finish", room_id=room_id).pack(),
                style=ButtonStyle.DANGER,
            )
        ]
    )
    return InlineKeyboardMarkup(inline_keyboard=rows)
